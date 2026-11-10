"""Run prior regression lanes with pre-collection storage isolation, no restore."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
from artifacts.pr_play_71v.regression import FOCUSED, BOUNDARY, BROADER


def run(label, files):
    xml = OUT / (label + ".xml")
    args = [sys.executable, "-m", "pytest", *files, "--tb=line", "--junitxml=" + str(xml), "--basetemp=" + str(OUT / (label + "_tmp"))]
    env = os.environ.copy()
    env["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
    with (OUT / (label + ".txt")).open("w", encoding="utf-8") as f:
        result = subprocess.run(args, cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT)
    root = ET.parse(xml).getroot()
    cases = list(root.iter("testcase"))
    return dict(command=args, exit_code=result.returncode, passed=sum(not any(c.find(tag) is not None for tag in ("failure", "error", "skipped")) for c in cases), failed=[c.get("classname", "") + "::" + c.get("name", "") for c in cases if c.find("failure") is not None or c.find("error") is not None])


if __name__ == "__main__":
    results = {}
    for name, files in [("focused", FOCUSED), ("boundary", BOUNDARY), ("broader", BROADER),
                        ("lifecycle_isolated", ["tests/test_pr_play_71_lifecycle.py", "tests/test_pr_play_71_persistence_recovery.py", "tests/test_pr_play_71v_verification.py"])]:
        results[name] = run(name, files)
        (OUT / "regression_results.json").write_text(json.dumps(results, indent=2))
        print(name, results[name]["passed"], len(results[name]["failed"]), flush=True)
