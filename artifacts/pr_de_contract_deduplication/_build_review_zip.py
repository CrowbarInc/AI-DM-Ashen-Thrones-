"""Refresh handoff/CURRENT_REVIEW.zip for PR-DE. No provider calls."""
from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoff"
OUT = Path(__file__).resolve().parent
AFFORD = ROOT / "artifacts" / "affordability"

FILES = [
    HANDOFF / "CURRENT_REVIEW.md",
    OUT / "PR-DE_implementation_report.md",
    OUT / "PR-DE_duplicate_verification.md",
    OUT / "PR-DE_consumer_audit.md",
    OUT / "PR-DE_semantic_preservation.md",
    OUT / "PR-DE_authority_controls.md",
    OUT / "PR-DE_benchmark_design.md",
    OUT / "PR-DE_hash_stability.md",
    OUT / "PR-DE_prompt_measurements.csv",
    OUT / "PR-DE_regression_results.md",
    OUT / "PR-DE_affordability_report.md",
    OUT / "PR-DE_remaining_risks.md",
    OUT / "focused_tests.txt",
    OUT / "changed_files.txt",
    AFFORD / "baseline" / "pr_de.json",
    AFFORD / "baseline" / "pr_de.csv",
    AFFORD / "post_change" / "pr_de.json",
    AFFORD / "post_change" / "pr_de.csv",
    ROOT / "tools" / "measure_pr_de_affordability.py",
]

manifest = {
    "pr": "PR-DE",
    "mode": "EXACT CONTRACT DEDUPLICATION AND AFFORDABILITY BASELINE",
    "decision": "A - EXACT DEDUPLICATION VERIFIED",
    "live_calls": 0,
    "inherited_decision": "B - PARTIAL ARCHITECTURE",
    "artifacts": [str(path.relative_to(ROOT)).replace("\\", "/") for path in FILES],
    "files": {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in FILES
    },
}
(HANDOFF / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

zip_path = HANDOFF / "CURRENT_REVIEW.zip"
tmp_path = HANDOFF / "CURRENT_REVIEW_prde.zip"
with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    archive.write(HANDOFF / "CURRENT_REVIEW.md", "CURRENT_REVIEW.md")
    archive.write(HANDOFF / "REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json")
    for path in FILES:
        if path.name == "CURRENT_REVIEW.md":
            continue
        archive.write(path, str(path.relative_to(ROOT)).replace("\\", "/"))
os.replace(tmp_path, zip_path)
print(zip_path, zip_path.stat().st_size)
