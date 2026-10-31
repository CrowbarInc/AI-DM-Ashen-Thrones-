"""Refresh handoff/CURRENT_REVIEW.zip for PR-DG. No provider calls."""
from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoff"
OUT = ROOT / "artifacts" / "pr_dg_architecture_preflight"

FILES = [
    HANDOFF / "CURRENT_REVIEW.md",
    OUT / "PR-DG_implementation_report.md",
    OUT / "PR-DG_runner_design.md",
    OUT / "PR-DG_candidate_A_results.md",
    OUT / "PR-DG_candidate_B_results.md",
    OUT / "PR-DG_candidate_C_results.md",
    OUT / "PR-DG_scenario_comparison.csv",
    OUT / "PR-DG_transaction_safety.md",
    OUT / "PR-DG_authority_controls.md",
    OUT / "PR-DG_interpretation_limitations.md",
    OUT / "PR-DG_cost_instrumentation.md",
    OUT / "PR-DG_regression_results.md",
    OUT / "PR-DG_remaining_risks.md",
    OUT / "focused_tests.txt",
    OUT / "changed_files.txt",
    OUT / "results.json",
    OUT / "pytest_counts.txt",
    ROOT / "tools" / "run_pr_dg_preflight.py",
    ROOT / "tests" / "test_pr_dg_architecture_preflight.py",
    ROOT / "experiments" / "__init__.py",
    ROOT / "experiments" / "pr_dg" / "__init__.py",
    ROOT / "experiments" / "pr_dg" / "isolation.py",
    ROOT / "experiments" / "pr_dg" / "state.py",
    ROOT / "experiments" / "pr_dg" / "resolve.py",
    ROOT / "experiments" / "pr_dg" / "candidate_b.py",
    ROOT / "experiments" / "pr_dg" / "candidate_c.py",
    ROOT / "experiments" / "pr_dg" / "scenarios.py",
    ROOT / "experiments" / "pr_dg" / "controls.py",
    ROOT / "experiments" / "pr_dg" / "runner.py",
    ROOT / "experiments" / "pr_dg" / "reports.py",
]

missing = [path for path in FILES if not path.is_file()]
if missing:
    raise SystemExit("missing: " + ", ".join(str(path) for path in missing))

manifest = {
    "pr": "PR-DG",
    "mode": "ARCHITECTURAL EXPERIMENT PREFLIGHT",
    "decision": "A - PREFLIGHT READY",
    "live_calls": 0,
    "inherited_decision": "A - COMPARISON READY",
    "artifacts": [str(path.relative_to(ROOT)).replace("\\", "/") for path in FILES],
    "files": {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in FILES
    },
}
(HANDOFF / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

zip_path = HANDOFF / "CURRENT_REVIEW.zip"
tmp_path = HANDOFF / "CURRENT_REVIEW_prdg.zip"
with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    archive.write(HANDOFF / "CURRENT_REVIEW.md", "CURRENT_REVIEW.md")
    archive.write(HANDOFF / "REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json")
    for path in FILES:
        if path.name == "CURRENT_REVIEW.md":
            continue
        archive.write(path, str(path.relative_to(ROOT)).replace("\\", "/"))
os.replace(tmp_path, zip_path)
print(zip_path, zip_path.stat().st_size)
