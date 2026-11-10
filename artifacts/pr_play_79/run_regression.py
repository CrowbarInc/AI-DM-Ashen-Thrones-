"""Regression lanes for PR-PLAY-79, compared with the PR-PLAY-78A identities."""
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
PRIOR = json.loads((ROOT / "artifacts" / "pr_play_78a" / "review_pack" / "machine" / "regression_results.json").read_text(encoding="utf-8"))


def run(label, files):
    xml = OUT / (label + ".xml")
    base = OUT / "regress" / label
    base.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, "-m", "pytest", *files, "--tb=line", "--junitxml=" + str(xml), "--basetemp=" + str(base)]
    env = os.environ.copy()
    env["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
    env["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
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
    prior = set(PRIOR.get(label, {}).get("failed", []))
    found = set(failed)
    return {
        "exit_code": result.returncode,
        "passed": sum(not any(case.find(tag) is not None for tag in ("failure", "error", "skipped")) for case in cases),
        "failed_count": len(failed),
        "failed": failed,
        "new_vs_pr_play_78a": sorted(found - prior),
        "cleared_vs_pr_play_78a": sorted(prior - found),
    }


if __name__ == "__main__":
    lanes = [("focused", FOCUSED), ("boundary", BOUNDARY), ("broader", BROADER)]
    selected = sys.argv[1:] or [name for name, _files in lanes]
    dest = OUT / "regression_results.json"
    results = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else {}
    for name, files in lanes:
        if name not in selected:
            continue
        results[name] = run(name, files)
        dest.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(name, results[name]["passed"], results[name]["failed_count"], "new", len(results[name]["new_vs_pr_play_78a"]), flush=True)
