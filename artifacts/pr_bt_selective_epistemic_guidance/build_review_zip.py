"""Build handoff/CURRENT_REVIEW.zip for the selective restoration. No model calls."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZIP_PATH = ROOT / "handoff" / "CURRENT_REVIEW.zip"
MANIFEST_PATH = ROOT / "handoff" / "REVIEW_MANIFEST.json"

FILES = [
    "handoff/CURRENT_REVIEW.md",
    "PR-BT_selective_epistemic_guidance_restoration_implementation.md",
    "PR-BT_selective_epistemic_protocol_diff.md",
    "artifacts/pr_bt_selective_epistemic_guidance/p1_p2_p3_measurements.json",
    "artifacts/pr_bt_selective_epistemic_guidance/regression_summary.json",
    "artifacts/pr_bt_selective_epistemic_guidance/regression.xml",
    "artifacts/pr_bt_selective_epistemic_guidance/system_prompt_excerpt.md",
    "tests/test_pr_bt_selective_epistemic_guidance.py",
    "artifacts/pr_bt_selective_epistemic_guidance/evidence/P1/provider_request_generation_1.json",
    "artifacts/pr_bt_selective_epistemic_guidance/evidence/P1/rule_presence.json",
    "artifacts/pr_bt_selective_epistemic_guidance/evidence/P2/provider_request_generation_1.json",
    "artifacts/pr_bt_selective_epistemic_guidance/evidence/P2/rule_presence.json",
    "artifacts/pr_bt_selective_epistemic_guidance/evidence/P3/provider_request_generation_1.json",
    "artifacts/pr_bt_selective_epistemic_guidance/evidence/P3/rule_presence.json",
]


def main() -> None:
    missing = [item for item in FILES if not (ROOT / item).is_file()]
    if missing:
        raise SystemExit("missing:\n" + "\n".join(missing))
    manifest = []
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in FILES:
            data = (ROOT / item).read_bytes()
            arc = "CURRENT_REVIEW.md" if item == "handoff/CURRENT_REVIEW.md" else item
            archive.writestr(arc, data)
            manifest.append({"path": arc, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        body = {
            "review": "PR-BT selective epistemic guidance restoration",
            "mode": "SELECTIVE RESTORATION IMPLEMENTATION",
            "model_api_calls": 0,
            "decision": "A - READY FOR REPEATED MICRO LIVE",
            "architecture": "A - PR-BR REMAINS CLOSED",
            "chars_restored": 552,
            "protocol_chars": 651,
            "tests_passed": 916,
            "tests_failed": 1,
            "c18": "PASS",
            "validators_changed": False,
            "retry_changed": False,
            "micro_live": "READY_NOT_RUN",
            "files": manifest,
        }
        encoded = json.dumps(body, indent=2).encode("utf-8")
        archive.writestr("REVIEW_MANIFEST.json", encoded)
    MANIFEST_PATH.write_bytes(encoded)
    print(f"wrote {ZIP_PATH} files={len(manifest)+1} bytes={ZIP_PATH.stat().st_size}")


if __name__ == "__main__":
    main()
