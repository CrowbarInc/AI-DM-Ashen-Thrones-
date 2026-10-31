"""Package PR-EF-R4 into the established CURRENT_REVIEW handoff."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import build_handoff

OUT = ROOT / "artifacts" / "pr_ef_r4"
summary = (OUT / "01_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
include = [
    p for p in OUT.rglob("*")
    if p.is_file()
    and "__pycache__" not in p.parts
    and p.name not in {"handoff_config.json", "package_review.py"}
]
config = {
    "campaign_id": "pr_ef_r4_authorization_contract_20261016",
    "campaign_name": "PR-EF-R4 — Conversational Authority Contract Consolidation",
    "campaign_date": "2026-10-16",
    "purpose": "Consolidate conversational authorization. Do not start PR-EG.",
    "objective_status": "B — PR-EF ACCEPTED WITH LIMITATIONS",
    "executive_summary": summary,
    "changes": {
        "production": [
            "One addressee grounding decision gates execution and the world tick.",
            "Provider NPC ids are candidates unless the utterance uniquely grounds them.",
            "Narration and retry are skipped only for a closed consequential-information plan.",
        ],
        "validation": [
            "Frozen holdouts in tests/fixtures/pr_ef_r4_holdouts.json.",
            "tests/test_pr_ef_r4_authorization.py.",
        ],
        "tooling": ["tools/validate_pr_ef_r4.py"],
        "documentation": ["Reports 01–18 under artifacts/pr_ef_r4."],
        "generated_artifacts": [
            "Fresh /api/chat conversation, holdouts, and performance records.",
            "Post-implementation regression junit.",
        ],
    },
    "testing": {
        "focused": "28/28 PR-EF-R4 authorization tests passed, including 25 frozen cases under scripted providers.",
        "broader": "Family 349 passed / 20 failed. The 20 identities are exactly the PR-EF-R2 historical set.",
        "full_suite": "Not run. The established conversational family was run.",
        "runtime_validation": "Fresh gpt-4.1-mini-2025-04-14 through TestClient /api/chat. Ten-turn conversation plus 25 live holdouts. 49 requests, 494725 input tokens.",
        "model_runtime_boundary": "Configured gpt-4.1-mini. Observed gpt-4.1-mini-2025-04-14.",
        "new_regressions": "None in the final family measurement.",
        "pre_existing_failures": "The twenty PR-EF-R2 identities remain. They were not cleaned up.",
    },
    "known_problems": {
        "campaign_specific": [
            "A cold follow-up can be blocked as malformed communication before continuation.",
            "A non-INTERPRETED record can speak the provider clarification instead of the authorization template.",
            "genuine_uncertainty and authoritative_answer_available with speech authority none still pay narration and retry.",
        ],
        "pre_existing": ["Twenty inherited regression failures from the R2 family."],
    },
    "missing_concepts": [
        "A non-persisted incidental speech lane. Left for PR-EG. Not implemented.",
    ],
    "decisions_requiring_human_review": [
        "Accept or reject B — accepted with limitations.",
        "Do not begin PR-EG from this package.",
    ],
    "does_not_prove": [
        "That every unknown question avoids narration.",
        "Interpretation-label agreement with the live model. Behavior is scored separately and is ahead of labels.",
        "A global token reduction against the R2 eleven-turn workload. The workloads differ.",
        "That the pre-edit tree would still score 321/20. That run was not repeated.",
    ],
    "recommended_next_step": "External review. Stop. Do not start PR-EG.",
    "primary_report": "artifacts/pr_ef_r4/01_EXECUTIVE_SUMMARY.md",
    "max_file_bytes": 5 * 1024 * 1024,
    "evidence_packets": [],
    "supporting_files": [
        {
            "path": p.relative_to(ROOT).as_posix(),
            "role": "source" if p.suffix == ".py" else "evidence",
            "why": "PR-EF-R4 report or fresh-provider evidence.",
            "behavioral_evidence": p.suffix in {".json", ".jsonl", ".xml"},
            "human_review_required": p.suffix == ".md",
        }
        for p in sorted(include)
    ],
    "self_contained_review_test": "Eighteen reports, frozen holdouts, live conversation, performance cases, and the regression junit. No .env and no active campaign saves.",
}
(OUT / "handoff_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
result = build_handoff(config, root=ROOT, output_dir=ROOT / "handoff", archive_history=True)
print(json.dumps({k: result[k] for k in ("summary_path", "zip_path", "file_count", "zip_size_bytes", "warning")}, indent=2))
