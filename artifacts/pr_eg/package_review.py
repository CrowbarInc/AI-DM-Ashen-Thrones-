"""Package PR-EG into the established CURRENT_REVIEW handoff."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import build_handoff

OUT = ROOT / "artifacts" / "pr_eg"
summary = (OUT / "01_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
include = [
    p for p in OUT.rglob("*")
    if p.is_file()
    and "__pycache__" not in p.parts
    and p.name not in {"handoff_config.json", "package_review.py"}
]
config = {
    "campaign_id": "pr_eg_dialogue_quality_20261016",
    "campaign_name": "PR-EG — Dialogue Quality and Bounded Improvisation",
    "campaign_date": "2026-10-16",
    "purpose": "Improve NPC dialogue relevance and bounded improvisation. Do not start PR-EH.",
    "objective_status": "C — PR-EG REQUIRES REPAIR",
    "executive_summary": summary,
    "changes": {
        "production": [
            "Dialogue-authority record distinguishes the requested information, NPC posture, and non-canonical speech.",
            "A topic answers a question only when it supports that request.",
            "Determined knowledge gaps skip narration. A harmless quoted remark can be kept without a retry.",
        ],
        "validation": [
            "Frozen holdouts in tests/fixtures/pr_eg_dialogue_holdouts.json.",
            "tests/test_pr_eg_dialogue_quality.py scores dimensions separately.",
        ],
        "tooling": ["tools/validate_pr_eg.py"],
        "documentation": ["Reports 01–18 under artifacts/pr_eg."],
        "generated_artifacts": [
            "Fresh /api/chat twelve-turn conversation before and after quote recovery.",
            "Baseline and post-implementation regression junit.",
        ],
    },
    "testing": {
        "focused": "73 passed, including frozen holdout dimensions and quote recovery. Provider not used for the holdout scorer.",
        "broader": "Family 350 passed / 19 failed. No new failing identities. One historical failure now passes.",
        "full_suite": "Not run. The established conversational family was run.",
        "runtime_validation": "Fresh gpt-4.1-mini-2025-04-14 through TestClient /api/chat. Twelve turns, 16 calls, 145400 input tokens, one retry.",
        "model_runtime_boundary": "Configured gpt-4.1-mini. Observed gpt-4.1-mini-2025-04-14.",
        "new_regressions": "None in the final family measurement.",
        "pre_existing_failures": "Nineteen of the twenty PR-EF-R2 identities remain. One, the repeated-question clean refusal, now passes.",
    },
    "known_problems": {
        "campaign_specific": [
            "A road-watch follow-up was answered with internal authority language and was not Mara's line.",
            "The follow-up to the road's name forgot that answer and spent a narration plus retry.",
            "A preference question stayed ignorance after one narration.",
            "A clarification was treated as an undo, and a promise request was answered as an unavailable action.",
        ],
        "pre_existing": ["Nineteen inherited regression failures from the R2 family."],
    },
    "missing_concepts": [
        "Using a public scene sentence, such as Mara looking concerned, as a partial spoken answer.",
        "A prompt small enough that one social narration is not tens of thousands of input tokens.",
    ],
    "decisions_requiring_human_review": [
        "Accept or reject C — PR-EG requires repair.",
        "Do not begin PR-EH from this package.",
    ],
    "does_not_prove": [
        "That every follow-up stays with the NPC who just spoke.",
        "That two fresh runs of the same follow-up take the same route. Turn 3 differed between the two live runs.",
        "That save/load of commitments was exercised on the disposable live campaign. That campaign directory was removed. The unit test covers the session shape.",
        "That the nineteen remaining family failures are unchanged in their assertion text. Identities were compared. Bodies were not re-audited.",
    ],
    "recommended_next_step": "External review. Stop. Do not start PR-EH.",
    "primary_report": "artifacts/pr_eg/01_EXECUTIVE_SUMMARY.md",
    "max_file_bytes": 5 * 1024 * 1024,
    "evidence_packets": [],
    "supporting_files": [
        {
            "path": p.relative_to(ROOT).as_posix(),
            "role": "source" if p.suffix == ".py" else "evidence",
            "why": "PR-EG report or fresh-provider evidence.",
            "behavioral_evidence": p.suffix in {".json", ".jsonl", ".xml"},
            "human_review_required": p.suffix == ".md",
        }
        for p in sorted(include)
    ],
    "self_contained_review_test": "Eighteen reports, frozen holdouts referenced from the tests, two live conversations, and the regression junit. No .env and no active campaign saves.",
}
(OUT / "handoff_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
result = build_handoff(config, root=ROOT, output_dir=ROOT / "handoff", archive_history=True)
print(json.dumps({k: result[k] for k in ("summary_path", "zip_path", "file_count", "zip_size_bytes", "warning")}, indent=2))
