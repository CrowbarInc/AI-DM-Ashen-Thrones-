"""Package ATGB-03B infrastructure evidence; no providers or gameplay scoring."""
import collections
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.build_review_handoff import build_handoff
OUT = Path(__file__).parent


def read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def write(p, value):
    p.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


attempts = []
for path in sorted(OUT.glob("*.xml")):
    suite = ET.parse(path).getroot().find("testsuite")
    attempts.append({"path": path.relative_to(ROOT).as_posix(),
        **{key: int(suite.get(key)) for key in ("tests", "failures", "errors", "skipped")},
        "modules": dict(collections.Counter(c.get("classname") for c in suite.findall("testcase"))),
        "failed_tests": [{"module": c.get("classname"), "name": c.get("name")} for c in suite.findall("testcase") if c.find("failure") is not None]})
write(OUT / "validation_results.json", {"accounting_version": "ATGB-03B-1", "attempts": attempts,
    "current_lifecycle_dispatch_owner_readiness_checks": {"tests": 59, "passed": 59, "source": "surface_final.xml"},
    "regression": {"tests": 227, "passed": 225, "pre_existing_failures_reproduced_before_repair": 2, "source": "regression.xml"},
    "environmental_failure": "One isolated Windows os.replace permission error in all-scenario reset; targeted retry passed. Both records retained.",
    "initial_test_wiring_failure": "Four test-guard failures fixed by using captured production functions with a controlled transport; corrected suite passed.",
    "real_provider_requests": 0, "live_benchmark_executed": False, "full_suite": "not_run", "gameplay_performance_claim": False})
config = {
    "campaign_id": "atgb_03b_provider_accounting_integrity", "campaign_name": "ATGB-03B Provider Accounting Integrity",
    "campaign_date": "2026-10-18", "purpose": "Repair provider-request accounting across production dispatch owners and validate safe ATGB request bounds without live execution.",
    "objective_status": "IMPLEMENTED; CURRENT-SOURCE ACCOUNTING READINESS VERIFIED; REVIEW PENDING; NO LIVE EXECUTION",
    "executive_summary": "The existing budget owner now reserves allowance atomically and writes durable attempt identity before dispatch. Seven production owners, including startup preflight, share the lifecycle. Current source/readiness verification passes. Latest 59 lifecycle/owner/readiness checks pass; relevant regression run 225/227 with both failures reproduced before repair. One isolated Windows reset-write error passed targeted retry. No new provider requests, gameplay change, baseline run or score; original evidence preserved.",
    "changes": {
        "production": ["Provider budget admission/reservation, durable lifecycle, stable identity and idempotent completion; integrations at all seven known owners.", "S04.2 early-return path exposes existing performance fields and separately scoped accounting metadata; reply/decisions unchanged."],
        "validation": ["Deterministic successful/failed/interrupted/refused dispatch tests for every owner; concurrency, incomplete telemetry, ledger failure, readiness mutation and ATGB isolation/budget tests."],
        "tooling": ["ATGB readiness verifies guarded SDK sites and reviewed source hashes. Worker reconciles admissions, preserves host telemetry, receives remaining campaign budgets and deadline."],
        "documentation": ["Complete dispatch inventory, root-cause/correction report, session orientation and scope/comparability review."],
        "generated_artifacts": ["All test attempts, original-source comparison diff, payload AST checks, readiness/preservation records and standard handoff."]},
    "testing": {
        "focused": "Latest current lifecycle/dispatch-owner/readiness suite: 59 passed. ATGB accounting, infrastructure and readiness checks observed passing; see per-attempt JUnit records.",
        "broader": "227 relevant provider/gameplay/ATGB tests: 225 passed, 2 pre-existing failures reproduced using original budget/call_gpt in memory.",
        "full_suite": "Not run.", "runtime_validation": "Provider-disabled real chat/reset isolation and controlled provider stubs only; no live benchmark or real API request.",
        "model_runtime_boundary": "Original SDK call arguments/model routing unchanged at all seven dispatch owners; real-provider behavior unmeasured.",
        "new_regressions": "None established in the exercised scope. One Windows reset file-replacement error passed targeted retry; original failure retained.",
        "pre_existing_failures": "Exact routing metadata expectation and expression answer_sufficiency expectation both reproduce with pre-repair code."},
    "known_problems": {
        "campaign_specific": ["Accounting is process-local and opt-in; active accounting requires fresh durable ledger. No automatic resume of prior ledger.", "JSONL consumers must recognize lifecycle events; historical completion-only records cannot be retroactively certified.", "Changed application sources/unknown dispatch sites require renewed readiness review."],
        "pre_existing": ["Two reproduced regression failures remain unchanged.", "Windows isolated reset os.replace can fail transiently; targeted retry passed.", "Original ATGB baseline remains 15/37 captured, unscored, with S07/S09 opening delivery unmeasured."]},
    "decisions_requiring_human_review": ["Review infrastructure correction, dispatch coverage, telemetry compatibility and known limitations before any separately authorized ATGB continuation.", "Do not infer gameplay improvement or assign original conversational scores from accounting tests. All human judgments remain pending."],
    "missing_concepts": ["No account-wide/distributed request quota or automatic crash-resume accounting is implemented.", "Complete live baseline and authorized human scoring remain outside this pass."],
    "does_not_prove": ["Live-provider benchmark completion, conversational improvement, a gameplay score, new cost/latency measurements, or SDK transport-request counts.", "Completeness of historical ATGB-03 ledgers or same-trial S04 resume continuity.", "Budget safety of independently launched experimental utilities or arbitrary future provider code."],
    "recommended_next_step": "Await review. Do not run live ATGB, modify gameplay, or start Product Realization work. A later authorized continuation must use proven allowances, explicit deadlines and distinct S04 trial provenance.",
    "primary_report": "development/reports/atgb_03b_provider_accounting_integrity.md", "evidence_packets": [],
    "configuration_source": "tools/atgb/provider_accounting_integrity.json", "supporting_files": [],
    "self_contained_review_test": "ZIP includes all seven changed owners and budget source, reviewed-source manifest, before-source diff, tests and every JUnit attempt, complete dispatch inventory, preservation/AST checks, readiness, and original accounting reports. Manifest payload hashes verified after packaging."}
paths = {
    "game/provider_budget.py", "game/api.py", "game/api_upstream_preflight.py", "game/gm.py", "game/live_chat_interpretation.py",
    "game/expressive_dialogue.py", "game/semantic_interpreter.py", "game/host_constrained_candidates.py", "game/unified_semantic_planning.py",
    "tools/atgb/accounting.py", "tools/atgb/chat_worker.py", "tools/atgb/driver.py", "tools/atgb/provider_accounting_integrity.json",
    "tests/test_provider_accounting_integrity.py", "tests/test_atgb_accounting.py", "tests/test_atgb_infrastructure.py", "tests/test_atgb_readiness.py",
    "tests/test_model_routing_runtime.py", "tests/test_pr_eg_r3_r1_expression_semantics.py", "docs/NEXT_SESSION.md",
    "development/reports/atgb_03a_provider_accounting.md", "development/reports/atgb_03_initial_live_baseline.md",
    "artifacts/atgb/atgb_03a/accounting_readiness.json", "artifacts/atgb/atgb_03a/original_accounting_analysis.json",
    "artifacts/atgb/atgb_03/S03/provider_usage.jsonl", "artifacts/atgb/atgb_03/S04/provider_usage.jsonl", "artifacts/atgb/atgb_03/S04/transcript.md",
    "data/validation/review_handoffs/atgb_03b_provider_accounting_integrity.json"}
paths |= {p.relative_to(ROOT).as_posix() for p in OUT.glob("*") if p.is_file() and p.suffix in {".json", ".py", ".xml", ".diff"}
          and p.name not in {"bundle_verification.json", "handoff_build.json"}}
paths |= {p.relative_to(ROOT).as_posix() for p in (OUT / "source_before").rglob("*.py")}
for path in sorted(paths):
    config["supporting_files"].append({"path": path, "role": "provider_accounting_integrity_evidence",
        "why": "Review lifecycle safety, source scope/comparability and exact validation limits without live-provider claims.",
        "behavioral_evidence": path.endswith("transcript.md"), "human_review_required": path.endswith("transcript.md")})
config_path = ROOT / "data/validation/review_handoffs/atgb_03b_provider_accounting_integrity.json"
write(config_path, config)
stage = OUT / "review_stage"
result = build_handoff(config, root=ROOT, output_dir=stage, archive_history=False)
# Windows can refuse truncating an existing open ZIP; install a completed file
# atomically instead. This does not modify the standard generator.
for name in ("CURRENT_REVIEW.md", "REVIEW_MANIFEST.json", "CURRENT_REVIEW.zip"):
    os.replace(stage / name, ROOT / "handoff" / name)
history = ROOT / "handoff/history" / config["campaign_id"]
history.mkdir(parents=True, exist_ok=True)
for source, target in (("CURRENT_REVIEW.md", "REVIEW.md"), ("REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json"), ("CURRENT_REVIEW.zip", "REVIEW.zip")):
    shutil.copyfile(ROOT / "handoff" / source, history / target)
result["installed_output_directory"] = str(ROOT / "handoff")
write(OUT / "handoff_build.json", result)
manifest = read(ROOT / "handoff/REVIEW_MANIFEST.json")
with zipfile.ZipFile(ROOT / "handoff/CURRENT_REVIEW.zip") as archive:
    checked = 0
    for row in manifest["included_files"]:
        if row.get("canonical"):
            blob = archive.read(row["bundle_path"])
            assert hashlib.sha256(blob).hexdigest() == row["sha256"]
            checked += 1
    assert "NO LIVE EXECUTION" in archive.read("CURRENT_REVIEW.md").decode()
write(OUT / "bundle_verification.json", {"verified": True, "canonical_files_verified": checked,
    "zip_sha256": hashlib.sha256((ROOT / "handoff/CURRENT_REVIEW.zip").read_bytes()).hexdigest(),
    "live_requests": 0, "gameplay_scores": None})
print(json.dumps({"verified": True, "files": checked}))
