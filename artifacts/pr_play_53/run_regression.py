"""Regression for PR-PLAY-53. Does not call a live provider."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_53"
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
PROTECT = [
    ROOT / "artifacts" / "pr_play_49" / "evidence_performance.json",
    ROOT / "artifacts" / "pr_play_47" / "evidence_performance.json",
    ROOT / "artifacts" / "pr_play_52" / "integration_results.json",
    ROOT / "artifacts" / "pr_play_50" / "requests.json",
]


def snapshot(paths):
    saved = {}
    for path in paths:
        if path.is_file():
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


def main() -> int:
    saved = snapshot(PROTECT)
    xml_path = OUT / "focused.xml"
    log_path = OUT / "focused.txt"
    basetemp = ROOT / "development" / "tmp" / f"pr_play_53_pytest_{os.getpid()}"
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
        "new_tests_file": "tests/test_pr_play_53_quarantined_live.py",
        "predecessor_passed_failed": "402 passed / 3 failed",
        "provider_calls": "disabled; this process did not make a live narration request",
        "restored": restore(saved),
        "command": args,
    }
    (OUT / "regression_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("collected", "passed", "failed", "errors", "skipped", "new_failures", "preexisting_failures_seen", "restored")}, indent=2))
    return 0 if not summary["new_failures"] and summary["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
