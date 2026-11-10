"""Regression and corpus metrics for PR-PLAY-54. Does not call a live provider."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_54"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ.pop("ASHEN_QUARANTINE_INVESTIGATION_NARRATION", None)
os.environ.pop("ASHEN_QUARANTINE_NARRATION_LIVE", None)
os.environ.pop("ASHEN_PROVIDER_USAGE_PATH", None)
os.environ.pop("ASHEN_PROVIDER_REQUEST_LIMIT", None)

SUITES = [
    "tests/test_pr_play_54_consequential_validation.py",
    "tests/test_pr_play_53_quarantined_live.py",
    "tests/test_pr_play_52_quarantined_integration.py",
    "tests/test_pr_play_42_evidence_boundaries.py",
    "tests/test_pr_play_51_geography_grounding.py",
    "tests/test_pr_play_49_anchored_narration.py",
    "tests/test_pr_play_47_controlled_renderer.py",
    "tests/test_pr_play_45_narration_authority.py",
    "tests/test_pr_play_46_mechanical_boundary.py",
    "tests/test_pr_play_44_information_delivery.py",
    "tests/test_pr_bu_lexical_scope.py",
    "tests/test_provider_accounting_integrity.py",
    "tests/test_pr_bw_narration_only_envelope.py",
    "tests/test_diegetic_fallback_narration.py",
    "tests/test_narration_state_consistency.py",
]
PRIOR = {
    "tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution",
    "tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues",
    "tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues",
}
PROTECT_ROOTS = [
    ROOT / "artifacts" / "pr_play_49",
    ROOT / "artifacts" / "pr_play_47",
    ROOT / "artifacts" / "pr_play_52",
    ROOT / "artifacts" / "pr_play_50",
]


def snapshot(roots):
    saved = {}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                saved[path] = path.read_bytes()
    return saved


def restore(saved) -> list[str]:
    restored = []
    for path, content in saved.items():
        if not path.exists() or path.read_bytes() != content:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            restored.append(path.relative_to(ROOT).as_posix())
    return restored


def metrics() -> dict:
    from game.anchored_investigation_narration import validate_prelude
    from game.consequential_narration_validation import validate_consequential_narration
    from game.immutable_valid_response import validate_generated_response
    from game.resolution_contract import contract_mapping_from_resolution
    from tests.pr_play_54_corpus import CASES, authority_for, contract_for, resolution_for

    rows = []
    started = time.perf_counter()
    for case in CASES:
        authority = authority_for(case["authority"])
        one = time.perf_counter()
        actual = validate_consequential_narration(case["text"], authority)
        elapsed_ms = (time.perf_counter() - one) * 1000
        resolution = resolution_for(case["authority"])
        previous = validate_generated_response(
            case["text"],
            resolution=resolution,
            contract=contract_mapping_from_resolution(resolution),
        )
        combined = None
        if case["authority"] in {"notice_success", "notice_failed", "notice_observed", "footprint", "guard_route"}:
            _, audit = validate_prelude(contract_for(case["authority"]), case["text"])
            combined = {
                "hard_valid": audit["hard_valid"],
                "reasons": audit["reasons"],
                "decision": audit["consequential_validation"]["decision"],
            }
        rows.append({
            "id": case["id"],
            "category": case["category"],
            "group": case["group"],
            "authority": case["authority"],
            "text": case["text"],
            "expected": case["expected"],
            "reason": case.get("reason"),
            "actual_decision": actual["decision"],
            "actual_reasons": actual["reasons"],
            "claims": actual["claims"],
            "latency_ms": round(elapsed_ms, 3),
            "provider_requests": actual["provider_requests"],
            "previous_decision": "FAIL" if not previous["hard_valid"] else "PASS",
            "previous_reasons": previous["reasons"],
            "combined_gate": combined,
        })
    total_ms = (time.perf_counter() - started) * 1000
    negatives = [row for row in rows if row["group"] == "negative"]
    positives = [row for row in rows if row["group"] in {"positive", "paraphrase"}]
    paraphrases = [row for row in rows if row["group"] == "paraphrase"]
    detected = [row for row in negatives if row["actual_decision"] in {"FAIL", "REVIEW_REQUIRED"}]
    false_negatives = [row for row in negatives if row["actual_decision"] == "PASS"]
    false_positives = [row for row in positives if row["actual_decision"] != "PASS"]
    reviews = [row for row in rows if row["actual_decision"] == "REVIEW_REQUIRED"]
    errors = [row for row in rows if row["actual_decision"] == "VALIDATION_ERROR"]
    paraphrase_accepted = [row for row in paraphrases if row["actual_decision"] == "PASS"]
    previous_detected = [row for row in negatives if row["previous_decision"] == "FAIL"]
    previous_false_negatives = [row for row in negatives if row["previous_decision"] == "PASS"]
    combined_false_positives = [
        row for row in positives
        if row["combined_gate"] is not None and row["combined_gate"]["hard_valid"] is False
    ]
    return {
        "cases": len(rows),
        "negative_cases": len(negatives),
        "positive_cases": len(positives),
        "paraphrase_cases": len(paraphrases),
        "detection_numerator": len(detected),
        "detection_denominator": len(negatives),
        "false_negatives": [row["id"] for row in false_negatives],
        "false_positive_ids": [row["id"] for row in false_positives],
        "false_positive_count": len(false_positives),
        "false_positive_denominator": len(positives),
        "review_required_ids": [row["id"] for row in reviews],
        "review_required_count": len(reviews),
        "validation_error_count": len(errors),
        "paraphrase_accepted": len(paraphrase_accepted),
        "paraphrase_denominator": len(paraphrases),
        "previous_detection_numerator": len(previous_detected),
        "previous_detection_denominator": len(negatives),
        "previous_false_negative_ids": [row["id"] for row in previous_false_negatives],
        "combined_gate_false_positive_ids": [row["id"] for row in combined_false_positives],
        "latency_ms_sum": round(sum(row["latency_ms"] for row in rows), 3),
        "latency_ms_max": round(max(row["latency_ms"] for row in rows), 3),
        "latency_ms_mean": round(sum(row["latency_ms"] for row in rows) / len(rows), 3),
        "corpus_wall_ms": round(total_ms, 3),
        "provider_requests": sum(row["provider_requests"] for row in rows),
        "rows": rows,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    measured = metrics()
    rows = measured.pop("rows")
    (OUT / "corpus_results.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    (OUT / "metrics.json").write_text(json.dumps(measured, indent=2) + "\n", encoding="utf-8")
    saved = snapshot(PROTECT_ROOTS)
    xml_path = OUT / "focused.xml"
    log_path = OUT / "focused.txt"
    basetemp = ROOT / "development" / "tmp" / f"pr_play_54_pytest_{os.getpid()}"
    args = [sys.executable, "-m", "pytest", *SUITES, "--tb=line", f"--junitxml={xml_path}", "--basetemp", str(basetemp)]
    with log_path.open("w", encoding="utf-8") as log:
        completed = subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy())
    root = ET.parse(xml_path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    counts = {key: int(suite.attrib.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")}
    failed = []
    for case in suite.iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(case.attrib.get("classname", "") + "::" + case.attrib.get("name", ""))
    summary = {
        "collected": counts["tests"],
        "failed": counts["failures"],
        "errors": counts["errors"],
        "skipped": counts["skipped"],
        "passed": counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"],
        "exit_code": completed.returncode,
        "failed_nodeids": failed,
        "preexisting_failures_seen": [name for name in failed if name in PRIOR],
        "new_failures": [name for name in failed if name not in PRIOR],
        "new_tests_file": "tests/test_pr_play_54_consequential_validation.py",
        "predecessor_passed_failed": "423 passed / 3 failed",
        "provider_calls": "disabled; this process did not make a live narration request",
        "restored": restore(saved),
        "command": args,
        "metrics": measured,
    }
    (OUT / "regression_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "collected": summary["collected"],
        "passed": summary["passed"],
        "failed": summary["failed"],
        "errors": summary["errors"],
        "skipped": summary["skipped"],
        "new_failures": summary["new_failures"],
        "preexisting": summary["preexisting_failures_seen"],
        "restored_count": len(summary["restored"]),
        "detection": [measured["detection_numerator"], measured["detection_denominator"]],
        "previous_detection": [measured["previous_detection_numerator"], measured["previous_detection_denominator"]],
        "false_negatives": measured["false_negatives"],
        "false_positives": measured["false_positive_ids"],
        "review": measured["review_required_ids"],
        "paraphrase": [measured["paraphrase_accepted"], measured["paraphrase_denominator"]],
        "combined_false_positives": measured["combined_gate_false_positive_ids"],
        "latency_mean_ms": measured["latency_ms_mean"],
        "provider_requests": measured["provider_requests"],
    }, indent=2))
    return 0 if not summary["new_failures"] and summary["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
