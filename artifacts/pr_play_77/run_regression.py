"""Isolated PR-PLAY-77 regression lanes. Baselines live outside artifacts."""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from artifacts.pr_play_71v.regression import BOUNDARY, BROADER, FOCUSED

OUT = Path(__file__).resolve().parent
BASE = ROOT / "development" / "tmp" / "pr77_regression"
BASE.mkdir(parents=True, exist_ok=True)


def run(label, files):
    xml = OUT / (label + ".xml")
    args = [
        sys.executable,
        "-m",
        "pytest",
        *files,
        "--tb=line",
        "--junitxml=" + str(xml),
        "--basetemp=" + str(BASE / label),
    ]
    env = os.environ.copy()
    env["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
    env.pop("ASHEN_TEST_EVIDENCE_DIR", None)
    log = OUT / (label + ".txt")
    with log.open("w", encoding="utf-8") as handle:
        result = subprocess.run(args, cwd=ROOT, env=env, stdout=handle, stderr=subprocess.STDOUT)
    root = ET.parse(xml).getroot()
    cases = list(root.iter("testcase"))
    failed = [
        (case.get("classname") or "") + "::" + (case.get("name") or "")
        for case in cases
        if case.find("failure") is not None or case.find("error") is not None
    ]
    return {
        "exit_code": result.returncode,
        "passed": sum(
            not any(case.find(tag) is not None for tag in ("failure", "error", "skipped"))
            for case in cases
        ),
        "failed_count": len(failed),
        "failed": failed,
    }


if __name__ == "__main__":
    lanes = [
        ("focused", FOCUSED),
        ("boundary", BOUNDARY),
        ("broader", BROADER),
        (
            "lifecycle_isolated",
            [
                "tests/test_pr_play_71_lifecycle.py",
                "tests/test_pr_play_71_persistence_recovery.py",
                "tests/test_pr_play_71v_verification.py",
            ],
        ),
    ]
    selected = sys.argv[1:] or [name for name, _files in lanes]
    results = {}
    dest = OUT / "regression_results.json"
    if dest.exists():
        results = json.loads(dest.read_text(encoding="utf-8"))
    for name, files in lanes:
        if name not in selected:
            continue
        results[name] = run(name, files)
        dest.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(name, results[name]["passed"], results[name]["failed_count"], flush=True)
