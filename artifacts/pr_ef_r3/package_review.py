"""Package PR-EF-R3 into the established CURRENT_REVIEW handoff."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import build_handoff

OUT = ROOT / "artifacts" / "pr_ef_r3"
summary = (OUT / "01_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
include = [
    p for p in OUT.rglob("*")
    if p.is_file()
    and "__pycache__" not in p.parts
    and "disposable_state" not in p.parts
    and p.name not in {"failure_provenance.json", "failure_summary.txt", "handoff_config.json"}
]
config = {
    "campaign_id": "pr_ef_r3_semantic_authority_20261016",
    "campaign_name": "PR-EF-R3 — Semantic Authority and Dialogue Overhead",
    "campaign_date": "2026-10-16",
    "purpose": "Investigation only. Choose localized repair, contract consolidation, or redesign. No production changes.",
    "objective_status": "B — CONTRACT CONSOLIDATION",
    "executive_summary": summary,
    "changes": {
        "production": [],
        "validation": [],
        "tooling": [],
        "documentation": ["Investigation reports under artifacts/pr_ef_r3."],
        "generated_artifacts": ["CURRENT_REVIEW package. Disposable interpretation probes and contract replays."],
    },
    "testing": {
        "focused": "No new production tests. R2 source hashes unchanged, so the 321/20 family was not re-run.",
        "broader": "Last measured family remains 321 pass / 20 fail. Not re-executed.",
        "full_suite": "Not run.",
        "runtime_validation": "Captured-record replay, two-NPC contract override, and 10 fresh interpretation-only probes. No new /api/chat campaign.",
        "model_runtime_boundary": "gpt-4.1-mini, observed gpt-4.1-mini-2025-04-14. Fresh probes: 10 requests, 16530 input, 1900 output.",
        "new_regressions": "None introduced. No production edit.",
        "pre_existing_failures": "20 inherited from PR-EF-R2. Not reclassified.",
    },
    "known_problems": {
        "campaign_specific": [
            "Unresolved plural address can be executed when the provider supplies a visible id.",
            "GM recipient can discard a direct NPC ask.",
            "Blocked interpretations are re-answered by evidence concatenation.",
            "Knowledge-gap NPC turns spend about 50k input tokens to show a template sentence.",
        ],
        "pre_existing": ["Twenty inherited regression failures from the R2 family."],
    },
    "missing_concepts": [
        "One authorization record for addressee status, owner, and mutation eligibility.",
        "A non-persisted incidental speech lane that is distinct from canonical facts.",
    ],
    "decisions_requiring_human_review": [
        "Accept or reject B — contract consolidation before any implementation.",
        "Do not begin PR-EG from this package.",
    ],
    "does_not_prove": [
        "Universal semantic reliability.",
        "A measured section-by-section split of the 23k-token social prompts.",
        "That a future consolidation will pass the regression family. That family was not re-run.",
        "Full HTTP play of the fresh probes.",
    ],
    "recommended_next_step": "External review. Stop. Implement the authorization record only after that review.",
    "primary_report": "artifacts/pr_ef_r3/REVIEW.md",
    "max_file_bytes": 5 * 1024 * 1024,
    "evidence_packets": [],
    "supporting_files": [
        {
            "path": p.relative_to(ROOT).as_posix(),
            "role": "source" if p.suffix == ".py" else "evidence",
            "why": "PR-EF-R3 investigation report or reproduction evidence.",
            "behavioral_evidence": p.suffix in {".json", ".jsonl"},
            "human_review_required": p.suffix == ".md",
        }
        for p in sorted(include)
    ],
    "self_contained_review_test": "Sixteen reports, contract replay, two-NPC override, token join, and fresh interpretation probes. No .env, active saves, or production diff.",
}
(OUT / "handoff_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
result = build_handoff(config, root=ROOT, output_dir=ROOT / "handoff", archive_history=True)
print(json.dumps({k: result[k] for k in ("summary_path", "zip_path", "file_count", "zip_size_bytes", "warning")}, indent=2))
