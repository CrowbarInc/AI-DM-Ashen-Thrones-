"""Bounded repeats of the historical rejected-publication HTTP case."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
NODE = "tests/test_pr_play_66_publication.py::test_publication_http[rejected]"
ATTEMPTS = 8
rows = []
for index in range(1, ATTEMPTS + 1):
    log = OUT / f"publication_500_attempt_{index}.txt"
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", NODE, "--tb=short", "--basetemp", str(OUT / f"basetemp_pub_{index}")],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    log.write_text(completed.stdout, encoding="utf-8")
    failed = completed.returncode != 0
    rows.append({
        "attempt": index,
        "exit_code": completed.returncode,
        "failed": failed,
        "traceback_present": "Traceback" in completed.stdout or "E   " in completed.stdout,
        "http_500_mentioned": "500" in completed.stdout and failed,
    })
    print(index, completed.returncode, flush=True)
summary = {
    "node": NODE,
    "attempts": ATTEMPTS,
    "failures": sum(row["failed"] for row in rows),
    "rows": rows,
    "reproduced": any(row["failed"] for row in rows),
    "note": "A passing repeat does not prove the historical HTTP 500 cause is identified.",
}
(OUT / "publication_500_diagnostics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps({k: summary[k] for k in ("attempts", "failures", "reproduced")}))
