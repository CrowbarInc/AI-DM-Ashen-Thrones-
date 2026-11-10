"""Replay the PR-PLAY-11/12 regression selection against current source."""
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_13"
lanes = json.loads((ROOT / "artifacts/pr_play_11/regression_runs.json").read_text(encoding="utf-8"))
PREEXISTING = {
    "tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution",
    "tests.test_pr_br_continuation18_immutable_boundary::test_raw_chat_stub_preserves_valid_and_contains_invalid",
    "tests.test_start_campaign_api::test_start_campaign_emits_opening_and_sets_started",
    "tests.test_start_campaign_api::test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text",
    "tests.test_start_campaign_api::test_start_campaign_promotes_valid_upstream_prepared_scene_opening",
    "tests.test_atgb_accounting::test_readiness_verifies_repaired_dispatch_coverage",
    "tests.test_pr_br_claim_control_slice2::test_false_positive_controls_remain_speakable",
    "tests.test_realization_provenance::test_call_gpt_provider_failure_metadata_has_provider_family",
    "tests.test_investigation_result_provenance_non_invention::test_general_written_surface_question_discovers_authored_clue",
    "tests.test_investigation_result_provenance_non_invention::test_general_visible_evidence_may_be_reported",
    "tests.test_investigation_result_provenance_non_invention::test_general_valid_target_no_evidence_is_grounded_absence",
    "tests.test_investigation_result_provenance_non_invention::test_general_requested_identity_absent_does_not_mint_person",
    "tests.test_investigation_result_provenance_non_invention::test_general_observe_empty_target_does_not_invent",
    "tests.test_investigation_result_provenance_non_invention::test_frontier_gate_t15_look_toward_does_not_mint_personnel_timing",
}
results = {}
env = {**os.environ, "ASHEN_DISABLE_PROVIDER_RETRIES": "1", "ASHEN_PLAYTEST_DISABLE_SDK_RETRIES": "1"}
env.pop("ASHEN_OPENING_RENDERER", None)
for name, row in lanes.items():
    if name == "entry_claim_authority":
        continue
    files = [item for item in row["command"] if str(item).startswith("tests/")]
    junit = OUT / f"{name}_regression.xml"
    cmd = [sys.executable, "-m", "pytest", *files, "-q", "--tb=line", f"--junitxml={junit}"]
    started = time.monotonic()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, env=env)
    (OUT / f"{name}_regression.txt").write_bytes(proc.stdout + b"\n" + proc.stderr)
    failures = []
    if junit.exists():
        root = ET.parse(junit).getroot()
        for case in root.iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                node = f"{case.get('classname')}::{case.get('name')}"
                failures.append(node)
    results[name] = {
        "exit": proc.returncode,
        "seconds": round(time.monotonic() - started, 2),
        "files": files,
        "failures": failures,
    }
    print(name, proc.returncode, results[name]["seconds"], len(failures), flush=True)
classified = []
for name, row in results.items():
    for test in row["failures"]:
        kind = "preexisting" if test in PREEXISTING else "new regression"
        classified.append({"lane": name, "test": test, "classification": kind})
summary = {
    "lanes": results,
    "failures": classified,
    "new_regressions": [row for row in classified if row["classification"] != "preexisting"],
    "preexisting": [row for row in classified if row["classification"] == "preexisting"],
}
(OUT / "regression_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print("new", len(summary["new_regressions"]), "preexisting", len(summary["preexisting"]))
