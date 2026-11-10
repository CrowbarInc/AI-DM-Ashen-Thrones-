"""Historical lanes for PR-PLAY-79D-F3. Provider calls stay disabled."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from artifacts.pr_play_79c import run_regression as runner

runner.OUT = Path(__file__).resolve().parent / "historical"
runner.OUT.mkdir(parents=True, exist_ok=True)
lanes = [("focused", runner.FOCUSED), ("boundary", runner.BOUNDARY), ("broader", runner.BROADER)]
results = {}
dest = runner.OUT / "regression_results.json"
for name, files in lanes:
    results[name] = runner.run(name, files)
    dest.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(name, results[name]["passed"], results[name]["failed_count"], "new", results[name]["new_vs_pr_play_78a"], flush=True)
