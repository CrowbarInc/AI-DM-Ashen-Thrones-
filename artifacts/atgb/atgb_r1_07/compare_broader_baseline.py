"""Repeat the same broader slice with entry production bytes; restore in finally."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
out = Path(__file__).parent
files = [ROOT / "game/live_chat_interpretation.py", ROOT / "game/conversational_orchestration.py"]
current = {p: p.read_bytes() for p in files}
command = [sys.executable, "-m", "pytest", "tests/test_pr_do_authority_separation.py", "tests/test_pr_dh_live_interpretation.py", "tests/test_live_model_guard.py", "tests/test_realization_provenance.py", "-vv", "-o", "faulthandler_timeout=30", "--basetemp=development/tmp/atgb_r1_07_broader_baseline", "--junitxml=artifacts/atgb/atgb_r1_07/broader_baseline.xml"]
try:
    for p in files:
        p.write_bytes((out / ("before_" + p.name)).read_bytes())
    with (out / "broader_baseline.txt").open("w", encoding="utf-8") as stream:
        result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=60)
    (out / "broader_baseline_exit.txt").write_text(str(result.returncode))
finally:
    for p, content in current.items():
        p.write_bytes(content)
print("Baseline comparison complete; repaired bytes restored.")
