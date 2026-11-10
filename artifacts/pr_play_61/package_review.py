"""Build the PR-PLAY-61 review handoff. No credentials."""
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import build_handoff

OUT = ROOT / "artifacts" / "pr_play_61"
REPORT = ROOT / "development/campaigns/product_realization/pr_play_61"
summary = (REPORT / "01_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
sources = [
    "game/api.py",
    "game/quarantined_investigation_narration.py",
    "game/integrated_investigation_narration.py",
    "tests/test_pr_play_61_player_facing.py",
    "docs/NEXT_SESSION.md",
    "artifacts/pr_play_61/experiment_results.json",
    "artifacts/pr_play_61/replay_results.json",
    "artifacts/pr_play_61/provider_usage.jsonl",
    "artifacts/pr_play_61/regression_summary_final.json",
    "artifacts/pr_play_61/focused_final.xml",
    "artifacts/pr_play_61/holdout_final.xml",
    "artifacts/pr_play_61/broader_hard_validation_final.xml",
    "artifacts/pr_play_61/frontend/player_log.png",
    "artifacts/pr_play_61/run_experiment.py",
    "artifacts/pr_play_61/replay_saved_narration.py",
]
paths = [ROOT / p for p in sources] + list(REPORT.glob("*.md"))
hits = []
for path in paths:
    if re.search(br"sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", path.read_bytes()):
        hits.append(path.relative_to(ROOT).as_posix())
if hits:
    raise SystemExit("sensitive material: " + ", ".join(hits))
config = {
    "campaign_id": "pr_play_61",
    "campaign_name": "PR-PLAY-61 — Controlled player-facing investigation",
    "campaign_date": "2026-11-03",
    "purpose": "Show a restricted investigation through the application, with validated narration or the engine fallback.",
    "objective_status": "A — PASS / CONTROLLED GAMEPLAY DEMONSTRATED",
    "executive_summary": summary,
    "primary_report": "development/campaigns/product_realization/pr_play_61/01_EXECUTIVE_SUMMARY.md",
    "evidence_packets": ["artifacts/pr_play_61"],
    "max_file_bytes": 33554432,
    "changes": {
        "production": ["Session-scoped publication of a passing investigation sentence, and engine fallback when the only ordinary sentence is the provider-disabled stub."],
        "validation": ["No validator change. PASS is still required before AI prose is published."],
        "tooling": ["One live four-action application run, saved-text replay, fault injection, and the prior focused regression."],
        "documentation": ["21 numbered reports and the session orientation."],
        "generated_artifacts": ["Provider ledger, per-action results, replay, regression summary, and the player-log screenshot."],
    },
    "testing": {
        "focused": "741 passed / 3 known failures of 744. Zero new focused failures.",
        "broader": "9/9 authority-assurance failures, each KeyError hard_validation_attempt_1.",
        "full_suite": "Not executed.",
        "runtime_validation": "Four live application actions, two published narrations, two engine fallbacks on replay, fault injection, and browser rendering.",
        "model_runtime_boundary": "OpenAI gpt-4.1-mini-2025-04-14. 4 requests, 1926 tokens, 0 retries.",
        "new_regressions": "None in the focused suite.",
        "pre_existing_failures": "3 focused failures and 9 broader hard_validation_attempt_1 failures.",
    },
    "decisions_requiring_human_review": ["No enablement of the flag for ordinary play. Quality scores are provisional."],
    "known_problems": {
        "campaign_specific": ["Rain-barrel and gate narration did not pass. The engine fallback lists every visible fact."],
        "pre_existing": ["3 focused failures, 9 broader metadata failures, H03 and H26 false rejections."],
    },
    "missing_concepts": ["A spoken fallback, a faster turn, and any mechanic beyond disclosure and observation."],
    "does_not_prove": ["General AI-DM play, inventory, NPC changes, travel, or an ATGB benchmark score."],
    "recommended_next_step": "Improve investigation responsiveness and replace the catalogue fallback with a short engine sentence. Do not expand the semantic validator.",
    "self_contained_review_test": "Reports, live results, replay, ledger, regression summary, and the player screenshot are included.",
    "supporting_files": [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "role": "source" if path.suffix == ".py" else "campaign_evidence",
            "why": "PR-PLAY-61 implementation, result, or report.",
            "human_review_required": True,
            "behavioral_evidence": path.suffix in {".json", ".jsonl", ".png", ".xml"},
        }
        for path in sorted(set(paths))
    ],
}
stage = OUT / "export_stage"
result = build_handoff(config, root=ROOT, output_dir=stage, archive_history=False)
for name in ("CURRENT_REVIEW.md", "REVIEW_MANIFEST.json", "CURRENT_REVIEW.zip"):
    (ROOT / "handoff" / name).write_bytes((stage / name).read_bytes())
stamp = datetime.now(timezone(timedelta(hours=-5))).strftime("%Y%m%d-%H%M%S")
archive = ROOT / "handoff" / f"CURRENT_REVIEW({stamp}).zip"
with archive.open("xb") as handle:
    handle.write((stage / "CURRENT_REVIEW.zip").read_bytes())
with zipfile.ZipFile(archive) as zipped:
    assert zipped.testzip() is None
    manifest = json.loads(zipped.read("REVIEW_MANIFEST.json"))
    for row in manifest["included_files"]:
        if row.get("sha256"):
            assert hashlib.sha256(zipped.read(row["bundle_path"])).hexdigest() == row["sha256"]
    reports = sum(
        "/pr_play_61/" in name and bool(re.search(r"/\d\d_[A-Z0-9_]+\.md$", name))
        for name in zipped.namelist()
    )
    assert reports == 21
    assert not any(".env" in name.split("/") for name in zipped.namelist())
record = {
    "path": str(archive),
    "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    "bytes": archive.stat().st_size,
    "crc_valid": True,
    "reports": reports,
    "omitted": result["omitted"],
}
(OUT / "archive_path.txt").write_text(str(archive) + "\n", encoding="utf-8")
(OUT / "archive_verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, indent=2))
