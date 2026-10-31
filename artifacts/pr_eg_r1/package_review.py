"""Package PR-EG-R1 into the established CURRENT_REVIEW handoff."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import build_handoff

OUT = ROOT / "artifacts" / "pr_eg_r1"
summary = (OUT / "01_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
include = [
    p for p in OUT.rglob("*")
    if p.is_file()
    and "__pycache__" not in p.parts
    and p.name not in {"handoff_config.json", "package_review.py"}
    and p.suffix != ".py"
]
config = {
    "campaign_id": "pr_eg_r1_conversational_continuity_20261016",
    "campaign_name": "PR-EG-R1 — Conversational Continuity and Response Ownership",
    "campaign_date": "2026-10-16",
    "purpose": "Repair conversational continuity and response ownership. Do not start PR-EH.",
    "objective_status": "B — PR-EG ACCEPTED WITH LIMITATIONS",
    "executive_summary": summary,
    "changes": {
        "production": [
            "Delivered NPC lines are the grounding source for the next turn.",
            "Ordinary NPC replies stay in the NPC's voice. GM recalls quote earlier speech.",
            "Topic corrections, harmless preferences, and reward requests no longer surface internal templates.",
        ],
        "validation": [
            "Frozen holdouts in tests/fixtures/pr_eg_r1_continuity_holdouts.json.",
            "Frozen live checks in tests/fixtures/pr_eg_r1_live_expectations.json.",
        ],
        "tooling": ["tools/validate_pr_eg_r1.py"],
        "documentation": ["Reports 01–19 under artifacts/pr_eg_r1."],
        "generated_artifacts": [
            "Fresh /api/chat fifteen-turn conversation and an independent twelve-turn conversation.",
            "Baseline and post-implementation regression junit.",
        ],
    },
    "testing": {
        "focused": "Continuity holdouts, PR-EG dialogue quality, and PR-EF-R4 authorization pass. Provider not used for the holdout scorer.",
        "broader": "Family 393 passed / 19 failed, including 22 new continuity tests. Pre-change family was 371 passed / 19 failed. No new failing identities.",
        "full_suite": "Not run. The established conversational family was run.",
        "runtime_validation": "Fresh gpt-4.1-mini through TestClient /api/chat. Fifteen turns, 6 calls, 56440 input tokens, 0 retries. Second conversation, 12 turns, 4 calls, 53374 input tokens, 0 retries. Frozen failures 0 and 0.",
        "model_runtime_boundary": "Configured gpt-4.1-mini. Observed route gpt-4.1-mini strict_social.",
        "new_regressions": "None in the final family measurement.",
        "pre_existing_failures": "The same nineteen identities as the pre-change baseline.",
    },
    "known_problems": {
        "campaign_specific": [
            "A paraphrase repeats the sentence under 'I meant this:' rather than restating it.",
            "The first street-name narration and the preference narration are still about 24k–26k input tokens each. They do not retry.",
        ],
        "pre_existing": ["Nineteen inherited regression failures from the shared turn pipeline and exploration routing."],
    },
    "missing_concepts": [
        "A real paraphrase of a delivered sentence.",
        "A smaller strict-social prompt for the first answer of a known fact.",
    ],
    "decisions_requiring_human_review": [
        "Accept or reject B — PR-EG accepted with limitations.",
        "Do not begin PR-EH from this package.",
    ],
    "does_not_prove": [
        "That every unseen phrasing will ground. Novel wording that matches neither a cue nor the supplied sentence still falls through to interpretation.",
        "That the first social narration can be cheap. Only follow-up retries were removed.",
        "That the nineteen remaining family failures are unchanged in their assertion text. Identities were compared.",
    ],
    "recommended_next_step": "External review. Stop. Do not start PR-EH.",
    "primary_report": "artifacts/pr_eg_r1/01_EXECUTIVE_SUMMARY.md",
    "max_file_bytes": 5 * 1024 * 1024,
    "evidence_packets": [],
    "supporting_files": [
        {
            "path": p.relative_to(ROOT).as_posix(),
            "role": "evidence",
            "why": "PR-EG-R1 report or fresh-provider evidence.",
            "behavioral_evidence": p.suffix in {".json", ".jsonl", ".xml"},
            "human_review_required": p.suffix == ".md",
        }
        for p in sorted(include)
    ],
    "self_contained_review_test": "Nineteen reports, frozen holdouts, two fresh /api/chat conversations, and the regression junit. No .env and no active campaign saves.",
}
(OUT / "handoff_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
result = build_handoff(config, root=ROOT, output_dir=ROOT / "handoff", archive_history=True)
print(json.dumps({k: result[k] for k in ("summary_path", "zip_path", "file_count", "zip_size_bytes", "warning")}, indent=2))
