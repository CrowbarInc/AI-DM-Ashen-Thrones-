"""Build the standard ATGB-03A handoff using explicit original evidence paths."""
import collections
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import build_handoff

OUT = Path(__file__).parent


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


prior = OUT / "prior_review"
prior.mkdir(exist_ok=True)
for name in ("CURRENT_REVIEW.md", "REVIEW_MANIFEST.json", "CURRENT_REVIEW.zip"):
    target = prior / name
    if not target.exists():
        shutil.copyfile(ROOT / "handoff" / name, target)
original = read(ROOT / "artifacts/atgb/atgb_03/configuration_and_provenance.json")
with zipfile.ZipFile(prior / "CURRENT_REVIEW.zip") as archive:
    for name in ("chat_worker.py", "driver.py"):
        blob = archive.read("support/tools/atgb/" + name)
        assert hashlib.sha256(blob).hexdigest() == original["source_sha256"]["tools/atgb/" + name]
        target = OUT / "original_harness" / name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(blob)
suite = ET.parse(OUT / "deterministic_host.xml").getroot().find("testsuite")
counts = collections.Counter(t.get("classname") for t in suite.findall("testcase"))
write(OUT / "validation_results.json", {
    "provider_disabled": True, "live_requests": 0,
    "tests": int(suite.get("tests")), "failures": int(suite.get("failures")),
    "errors": int(suite.get("errors")), "skipped": int(suite.get("skipped")),
    "counts_by_module": dict(counts), "junit": "artifacts/atgb/atgb_03a/deterministic_host.xml",
    "sandbox_attempt": "Interrupted during known TestClient startup stall; no complete result. Same focused suite passed outside sandbox.",
    "coverage_result": "unsafe_upper_bound_not_established", "broad_or_full_suite": "not_run"})
old_config = read(ROOT / "data/validation/review_handoffs/atgb_03_initial_live_baseline.json")
config = {
    "campaign_id": "atgb_03a_provider_accounting", "campaign_name": "ATGB-03A Provider Accounting Safety and Continuation Readiness",
    "campaign_date": "2026-10-18", "purpose": "Investigate accounting and continue only if request usage can be bounded safely.",
    "objective_status": "SAFETY CORRECTION VALIDATED; UPPER BOUND UNRESOLVED; LIVE CONTINUATION STOPPED",
    "executive_summary": "45 provider-disabled tests passed. Three production ledger coverage gaps prevent a safe upper bound. Benchmark entry points now refuse before live dispatch. No new live trials or requests; original 15/37 captured turns preserved. Human scoring pending. User's explicit stop condition applied; full accounting repair and live baseline remain incomplete.",
    "changes": {"production": ["None; source hashes match original execution."],
        "validation": ["21 new accounting checks plus 24 existing infrastructure/readiness checks passed."],
        "tooling": ["ATGB-03A-1 ledger observation/reconciliation and fail-closed readiness gate in runner and direct worker."],
        "documentation": ["Root-cause report, current session orientation, distinct-trial continuation plan."],
        "generated_artifacts": ["Coverage audit, preservation hashes, original raw metadata, usage/latency summaries, unchanged human worksheets and transcripts."]},
    "testing": {"focused": "45 passed, 0 failed/errors/skipped; provider-disabled.", "broader": "Existing provider-disabled chat and all-scenario reset checks included in 45.",
        "full_suite": "Not run.", "runtime_validation": "No additional live execution; original baseline remains partial.",
        "model_runtime_boundary": "Original OpenAI gpt-4.1-mini configuration preserved; zero new live calls.",
        "new_regressions": "None observed in focused scope; live execution intentionally unavailable until accounting is reliable.",
        "pre_existing_failures": "Host telemetry missing/incomplete scope; completion-ledger coverage gaps. Interrupted sandbox TestClient attempt retained as environmental limitation."},
    "known_problems": {"campaign_specific": ["Reliable universal request upper bound remains unresolved; live continuation refused.", "No supported S04.3 resume continuity; future S04 requires a separate full trial.", "S07/S09 opening context unmeasured."],
        "pre_existing": ["Original host counters omit expression usage; S04.2 performance absent.", "Ledger does not cover all dispatch owners and unfinished attempts.", "Dirty worktree, previously exposed held-out corpus, unavailable dollar costs/SDK retry counts."]},
    "decisions_requiring_human_review": ["Review the fail-closed safety correction and established accounting coverage limitations. No gameplay change proposed.", "Human-score original captured conversations only; retain pending/not-evaluated until authorized judgments are supplied."],
    "missing_concepts": ["Reliable dispatch lifecycle accounting across provider owners within an approved scope.", "Validated resume/checkpoint continuity; complete live baseline and human scoring."],
    "does_not_prove": ["Complete accounting repair or full live baseline completion.", "Zero provider use from absent host telemetry, or exact turn attribution from an untagged ledger.", "Gameplay improvement, semantic success, S07/S09 opening delivery, independent generalization, dollar cost, or SDK-internal retry totals."],
    "recommended_next_step": "Await review. Do not bypass guard or start gameplay/Product Realization repairs. If separately resolved, rerun S04 as trial 2 and execute S05–S10 with proven request allowance and fresh explicit deadlines, preserving S01–S03 and original partial S04.",
    "primary_report": "development/reports/atgb_03a_provider_accounting.md", "evidence_packets": [],
    "configuration_source": "artifacts/atgb/atgb_03a/continuation_plan.json",
    "supporting_files": [],
    "self_contained_review_test": "Bundle includes original captured transcripts/raw evidence/worksheets, original changed harness source snapshots, new accounting code/tests/JUnit, coverage audit, continuation plan and preservation checks. No human scores created. ZIP contents/hash verification recorded separately."}
paths = {row["path"] for row in old_config["supporting_files"]}
paths |= {"tools/atgb/accounting.py", "tools/atgb/chat_worker.py", "tools/atgb/driver.py", "tests/test_atgb_accounting.py", "docs/NEXT_SESSION.md"}
paths |= {p.relative_to(ROOT).as_posix() for p in OUT.glob("*") if p.suffix in {".json", ".md", ".py", ".xml"} and p.name not in {"handoff_build.json", "bundle_verification.json"}}
paths |= {p.relative_to(ROOT).as_posix() for p in (OUT / "original_harness").glob("*.py")}
for path in sorted(paths):
    config["supporting_files"].append({"path": path, "role": "accounting_infrastructure_and_original_trial_evidence",
        "why": "Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation.",
        "behavioral_evidence": "/transcript.md" in path, "human_review_required": "/transcript.md" in path or "/worksheet" in path})
config_path = ROOT / "data/validation/review_handoffs/atgb_03a_provider_accounting.json"
write(config_path, config)
result = build_handoff(config, root=ROOT, output_dir=ROOT / "handoff")
write(OUT / "handoff_build.json", result)
manifest = read(ROOT / "handoff/REVIEW_MANIFEST.json")
with zipfile.ZipFile(ROOT / "handoff/CURRENT_REVIEW.zip") as archive:
    checked = 0
    for row in manifest["included_files"]:
        if row.get("canonical"):
            assert hashlib.sha256(archive.read(row["bundle_path"])).hexdigest() == row["sha256"]
            checked += 1
    summary = archive.read("CURRENT_REVIEW.md").decode("utf-8")
    assert "UPPER BOUND UNRESOLVED" in summary
write(OUT / "bundle_verification.json", {"verified": True, "canonical_files_verified": checked,
    "zip_sha256": hashlib.sha256((ROOT / "handoff/CURRENT_REVIEW.zip").read_bytes()).hexdigest(),
    "human_scoring": "pending", "live_continuation": "not_executed"})
print(json.dumps({"verified": True, "files": checked}))
