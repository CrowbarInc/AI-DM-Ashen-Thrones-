import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
spec = json.loads(
    (root / "artifacts/pr_play_t06_persistent_manipulation/baseline_command.json").read_text(encoding="utf-8")
)
args = spec["args"]
nodes = args[: args.index("-q")]
out = Path(__file__).resolve().parent
cmd = [
    sys.executable,
    "-m",
    "pytest",
    *nodes,
    "-q",
    "--tb=line",
    "-p",
    "no:cacheprovider",
    "--junitxml=" + str(out / "before_combined_junit.xml"),
    "--basetemp=" + str(root / "development/tmp/marking_action_before_combined"),
]
raise SystemExit(subprocess.call(cmd, cwd=root))
