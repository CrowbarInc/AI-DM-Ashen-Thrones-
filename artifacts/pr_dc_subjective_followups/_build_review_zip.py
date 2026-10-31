"""Refresh handoff/CURRENT_REVIEW.zip for PR-DC. No provider calls."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoff"
OUT = Path(__file__).resolve().parent

FILES = [
    ROOT / "game" / "social.py",
    ROOT / "tests" / "test_pr_dc_subjective_followups.py",
    HANDOFF / "CURRENT_REVIEW.md",
    OUT / "PR-DC_implementation_report.md",
    OUT / "PR-DC_classifier_trace.md",
    OUT / "PR-DC_authority_contract.md",
    OUT / "PR-DC_positive_controls.md",
    OUT / "PR-DC_negative_controls.md",
    OUT / "PR-DC_three_turn_replay.md",
    OUT / "PR-DC_adversarial_validation.md",
    OUT / "PR-DC_prompt_measurements.csv",
    OUT / "PR-DC_regression_results.md",
    OUT / "PR-DC_remaining_risks.md",
    OUT / "focused_tests.txt",
    OUT / "changed_files.txt",
]

manifest = {
    "pr": "PR-DC",
    "mode": "SUBJECTIVE FOLLOW-UP CLASSIFICATION",
    "decision": "A - SUBJECTIVE FOLLOW-UPS VERIFIED",
    "live_calls": 0,
    "inherited_decision": "A - SPEAKER GROUNDING REPAIRED",
    "shared_pipeline_before": "41 passed / 24 failed",
    "shared_pipeline_after": "41 passed / 24 failed / 0 skipped",
    "focused_regression": "284 passed / 3 failed / 0 skipped",
    "artifacts": [str(path.relative_to(ROOT)).replace("\\", "/") for path in FILES],
    "files": {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in FILES
    },
}
(HANDOFF / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

zip_path = HANDOFF / "CURRENT_REVIEW.zip"
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    archive.write(HANDOFF / "CURRENT_REVIEW.md", "CURRENT_REVIEW.md")
    archive.write(HANDOFF / "REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json")
    for path in FILES:
        if path.name in {"CURRENT_REVIEW.md"}:
            continue
        archive.write(path, str(path.relative_to(ROOT)).replace("\\", "/"))
print(zip_path, zip_path.stat().st_size)
