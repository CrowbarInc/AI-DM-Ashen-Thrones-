"""Refresh handoff/CURRENT_REVIEW.zip for PR-DD. No provider calls."""
from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoff"
OUT = Path(__file__).resolve().parent

FILES = [
    HANDOFF / "CURRENT_REVIEW.md",
    OUT / "PR-DD_architecture_report.md",
    OUT / "PR-DD_provider_request_trace.md",
    OUT / "PR-DD_context_inventory.csv",
    OUT / "PR-DD_authority_dependency_matrix.csv",
    OUT / "PR-DD_redundancy_analysis.md",
    OUT / "PR-DD_context_contracts.md",
    OUT / "PR-DD_cost_model.md",
    OUT / "PR-DD_target_budgets.md",
    OUT / "PR-DD_implementation_options.md",
    OUT / "PR-DD_recommended_sequence.md",
    OUT / "PR-DD_affordability_benchmark.md",
    OUT / "PR-DD_remaining_risks.md",
    OUT / "changed_files.txt",
    OUT / "measure_pr_dd.py",
    OUT / "_inventory.json",
    OUT / "_build_review_zip.py",
]

manifest = {
    "pr": "PR-DD",
    "mode": "PROVIDER CONTEXT BUDGET ARCHITECTURE",
    "decision": "B - PARTIAL ARCHITECTURE",
    "live_calls": 0,
    "inherited_decision": "A - SUBJECTIVE FOLLOW-UPS VERIFIED",
    "implementation": "none",
    "artifacts": [str(path.relative_to(ROOT)).replace("\\", "/") for path in FILES],
    "files": {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in FILES
    },
}
(HANDOFF / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

zip_path = HANDOFF / "CURRENT_REVIEW.zip"
tmp_path = HANDOFF / "CURRENT_REVIEW_prdd.zip"
with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    archive.write(HANDOFF / "CURRENT_REVIEW.md", "CURRENT_REVIEW.md")
    archive.write(HANDOFF / "REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json")
    for path in FILES:
        if path.name == "CURRENT_REVIEW.md":
            continue
        archive.write(path, str(path.relative_to(ROOT)).replace("\\", "/"))
os.replace(tmp_path, zip_path)
print(zip_path, zip_path.stat().st_size)
