import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
spec = json.loads(
    (root / "artifacts/pr_play_t06_persistent_manipulation/baseline_command.json").read_text(encoding="utf-8")
)
nodes = spec["args"][: spec["args"].index("-q")]
out = Path(__file__).resolve().parent
cmd = [
    sys.executable, "-m", "pytest", *nodes, "-q", "--tb=line", "-p", "no:cacheprovider",
    "--junitxml=" + str(out / "after_combined_junit.xml"),
    "--basetemp=" + str(root / "development/tmp/marking_action_after_combined"),
]
raise SystemExit(subprocess.call(cmd, cwd=root))
