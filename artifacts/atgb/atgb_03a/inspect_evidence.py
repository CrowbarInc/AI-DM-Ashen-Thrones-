"""Read original ATGB-03 evidence; write ATGB-03A observations separately."""
import collections
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.atgb.accounting import live_accounting_readiness

OUT = Path(__file__).parent
OLD = ROOT / "artifacts/atgb/atgb_03"


def read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


audit = live_accounting_readiness(ROOT)
write("accounting_readiness.json", audit)
results = {p.parent.name: read(p) for p in sorted(OLD.glob("S*/result.json"))}
observations = []
usage = []
for sid, result in results.items():
    ledger = OLD / sid / "provider_usage.jsonl"
    records = [json.loads(line) for line in ledger.read_text().splitlines()]
    usage += [{"scenario_id": sid, **r} for r in records]
    host = [t["telemetry"]["provider_call_count"] for t in result["turns"]]
    observations.append({"scenario_id": sid, "host_known_call_subtotal": sum(f["value"] for f in host if f["status"] == "recorded"),
                         "host_unavailable_turn_counts": sum(f["status"] != "recorded" for f in host),
                         "ledger_observed_sent_subtotal": sum(r.get("sent") is True for r in records),
                         "request_upper_bound": None, "per_turn_ledger_attribution": "unavailable_original_ledger_has_no_turn_ids"})
worker_path = next((OLD / "S04/stores").glob("*/atgb-worker.json"))
worker = read(worker_path)
store = worker_path.parent
log = [json.loads(line) for line in (store / "session_log.jsonl").read_text().splitlines()]
last = log[-1]
write("original_accounting_analysis.json", {
    "source_trial": "ATGB-03/trial-1", "scenarios": observations,
    "observed_sent_requests": sum(r.get("sent") is True for r in usage),
    "purpose_counts": dict(collections.Counter(r["purpose"] for r in usage if r.get("sent"))),
    "request_upper_bound": None,
    "S04_2_raw_resolution": last.get("resolution"),
    "S04_2_worker_capture": worker["turns"][-1],
    "live_additional_requests_in_ATGB_03A": 0,
    "note": "Ledger subtotal is an observation. No missing performance field is filled from detail counters or inferred as zero. Original ledger lacks dispatch-start records and a runtime snapshot."})
write("continuation_plan.json", {
    "status": "blocked_accounting_coverage", "resume_S04_3_authorized_for_execution_now": False,
    "original_trial": "ATGB-03/trial-1", "original_S04_turns": [t["turn_id"] for t in results["S04"]["turns"]],
    "original_store": store.relative_to(ROOT).as_posix(),
    "resume_continuity": "not_established_by_supported_harness",
    "evidence": ["prepare_isolated_store rejects marked/reused campaign stores", "execute_job verifies authored baseline then unconditionally hard resets", "No resume/checkpoint mode or process-local accounting restoration exists"],
    "next_safe_trial_if_accounting_is_resolved": "S04/trial-2 from beginning in separate new isolated store; do not splice trial-1 responses",
    "remaining_scenarios": [f"S{i:02}" for i in range(4, 11)],
    "do_not_rerun": ["S01", "S02", "S03"],
    "production_revision": results["S04"]["repository_revision"], "baseline": results["S04"]["baseline"],
    "model_configuration": results["S04"]["model_configuration"],
    "original_limit": {"application_requests": 80, "elapsed_seconds": 1800},
    "future_budget_requirements": "Fresh explicit deadline and request limit must be established after reliable accounting; original wall-clock deadline has expired. 12 requests are observed, but 68 remaining is not a proven allowance until coverage is resolved.",
    "opening_context_capture": {sid: {"status": "not_evaluated", "delivered": None,
        "required": "Capture actual player-visible opening output and its raw source before turn 1; authored seed alone is insufficient. Do not inject narrative."} for sid in ("S07", "S09")}})
status = read(OLD / "scenario_status.json")
write("execution_status.json", {"status": "STOPPED_BEFORE_LIVE_CONTINUATION", "accounting_version": audit["version"],
    "correction": "benchmark-only fail-closed pre-execution guard and ledger reconciliation", "upper_bound_repair_complete": False,
    "live_continuation_completed": False, "new_live_trials": [], "additional_provider_requests": 0,
    "scenario_status": status, "captured_turns": 15, "uncaptured_turns": 22,
    "evaluated_successes": None, "evaluated_failures": None, "human_review": "pending",
    "gameplay_scores": None, "cost": {"status": "unavailable", "value": None},
    "limitation": "Existing ledger cannot safely establish request upper bound across production dispatch owners. User stop condition applied."})
# Original worksheets are copied byte-for-byte with their original trial identity.
for name in ("worksheet.md", "worksheet.json", "provider_telemetry.json", "turn_telemetry.json"):
    (OUT / ("original_" + name)).write_bytes((OLD / name).read_bytes())
before = read(OUT / "preservation_before.json")
changed = [name for name, digest in before.items() if sha(ROOT / name) != digest]
allowed = ["tools/atgb/chat_worker.py", "tools/atgb/driver.py"]
unexpected = [n for n in changed if n not in allowed]
historical = read(OLD / "configuration_and_provenance.json")
historical_drift = {group: [n for n, digest in historical[group].items()
                            if n not in allowed and sha(ROOT / n) != digest]
                    for group in ("source_sha256", "canonical_data_sha256")}
write("preservation_checks.json", {"original_evidence_unchanged": not any(n.startswith("artifacts/atgb/atgb_03/") or n == "development/reports/atgb_03_initial_live_baseline.md" for n in changed),
    "production_corpus_baseline_and_canonical_data_unchanged": not unexpected,
    "changed_preexisting_snapshot_files": changed, "unexpected_changes": unexpected,
    "drift_from_original_execution_except_declared_benchmark_changes": historical_drift,
    "new_infrastructure_sources": {n: sha(ROOT/n) for n in allowed + ["tools/atgb/accounting.py", "tests/test_atgb_accounting.py"]}})
assert not unexpected, unexpected
assert not any(historical_drift.values()), historical_drift
print(json.dumps({"coverage_ready": audit["ok"], "gaps": len(audit["established_gaps"]), "original_preserved": not unexpected}))
