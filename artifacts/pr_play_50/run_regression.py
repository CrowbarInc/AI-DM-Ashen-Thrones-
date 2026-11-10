"""Focused offline regression. Restores predecessor evidence the tests rewrite."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_50"
SUITES = [
    "tests/test_pr_play_49_anchored_narration.py",
    "tests/test_pr_play_47_controlled_renderer.py",
    "tests/test_pr_play_45_narration_authority.py",
    "tests/test_pr_play_44_information_delivery.py",
    "tests/test_pr_play_46_mechanical_boundary.py",
    "tests/test_provider_accounting_integrity.py",
    "tests/test_pr_bw_narration_only_envelope.py",
    "tests/test_diegetic_fallback_narration.py",
    "tests/test_narration_state_consistency.py",
]
PREEXISTING = {
    "tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues",
    "tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues",
}
PROTECT = [ROOT / "artifacts" / "pr_play_49", ROOT / "artifacts" / "pr_play_47"]


def snapshot(dirs):
    saved = {}
    for directory in dirs:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                saved[path] = path.read_bytes()
    return saved


def main() -> int:
    os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
    os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
    before = snapshot(PROTECT)
    xml_path = OUT / "focused.xml"
    log_path = OUT / "focused.txt"
    args = [sys.executable, "-m", "pytest", *SUITES, "--tb=line", f"--junitxml={xml_path}",
            "--basetemp", str(ROOT / "development" / "tmp" / "pr_play_50_pytest")]
    with log_path.open("w", encoding="utf-8") as log:
        run = subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy())
    restored = []
    for path, content in before.items():
        if not path.exists() or path.read_bytes() != content:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            restored.append(path.relative_to(ROOT).as_posix())
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
        "exit_code": run.returncode,
        "failed_nodeids": failed,
        "preexisting_failures_seen": [name for name in failed if name in PREEXISTING],
        "new_failures": [name for name in failed if name not in PREEXISTING],
        "predecessor_evidence_restored": restored,
        "provider_calls": "disabled for this process; no live provider request",
        "command": args,
    }
    (OUT / "regression_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("collected", "passed", "failed", "errors", "skipped", "new_failures", "preexisting_failures_seen")}, indent=2))
    return 0 if not summary["new_failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
