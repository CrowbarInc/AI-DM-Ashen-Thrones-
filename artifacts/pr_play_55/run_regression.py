"""Focused regression for PR-PLAY-55. Does not call a provider.

The frozen holdout test is not part of this command. It was executed once
before this runner, and its saved evaluation is copied into the summary.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_55"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ.pop("ASHEN_QUARANTINE_INVESTIGATION_NARRATION", None)
os.environ.pop("ASHEN_QUARANTINE_NARRATION_LIVE", None)

SUITES = [
    "tests/test_pr_play_55_discovery_claims.py",
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


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    saved = snapshot(PROTECT_ROOTS)
    xml_path = OUT / "focused.xml"
    log_path = OUT / "focused.txt"
    basetemp = ROOT / "development" / "tmp" / f"pr_play_55_pytest_{os.getpid()}"
    args = [sys.executable, "-m", "pytest", *SUITES, "--tb=line", f"--junitxml={xml_path}", "--basetemp", str(basetemp)]
    with log_path.open("w", encoding="utf-8") as log:
        completed = subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy())
    import xml.etree.ElementTree as ET

    root = ET.parse(xml_path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    counts = {key: int(suite.attrib.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")}
    failed = []
    for case in suite.iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(case.attrib.get("classname", "") + "::" + case.attrib.get("name", ""))
    evaluation = json.loads((OUT / "evaluation.json").read_text(encoding="utf-8"))
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
        "holdout_test": "executed once before this command; see evaluation.json",
        "holdout_mismatches": evaluation["holdout"]["mismatch_ids"],
        "provider_calls": "disabled; this process did not make a live narration request",
        "restored": restore(saved),
        "command": args,
    }
    (OUT / "regression_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "collected", "passed", "failed", "errors", "skipped", "new_failures", "preexisting_failures_seen",
    )}, indent=2))
    return 0 if not summary["new_failures"] and summary["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
