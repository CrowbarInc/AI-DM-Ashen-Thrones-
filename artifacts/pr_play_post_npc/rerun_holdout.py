"""Re-run the frozen 79D-F3 holdout into the post-NPC evidence directory.

Does not write artifacts/pr_play_79df3/holdout_results.jsonl.
Non-local socket connections are refused.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("ASHEN_DISABLE_PROVIDER_CALLS", None)

blocked_connections = []
_real_create_connection = socket.create_connection


def _guarded_create_connection(address, *args, **kwargs):
    host = address[0] if isinstance(address, tuple) else address
    if str(host) not in {"127.0.0.1", "localhost", "::1"}:
        blocked_connections.append(str(host))
        raise OSError(f"blocked a non-local connection to {host}")
    return _real_create_connection(address, *args, **kwargs)


socket.create_connection = _guarded_create_connection

from tests.helpers.storage_isolation import install

install(Path(tempfile.mkdtemp(prefix="post-npc-holdout-")))

from _pytest.monkeypatch import MonkeyPatch

from tests.test_pr_play_79df3_holdout import DIGEST, MANIFEST, _mismatch, _run

raw = MANIFEST.read_bytes()
digest = hashlib.sha256(raw).hexdigest()
assert digest == DIGEST.read_text(encoding="utf-8").strip()
manifest = json.loads(raw)
monkeypatch = MonkeyPatch()
results = []
for case in manifest["cases"]:
    monkeypatch.undo()
    try:
        actual = _run(case, OUT / "holdout_tmp" / case["id"], monkeypatch)
        errors = _mismatch(actual, case["expect"])
    except Exception as exc:  # noqa: BLE001
        actual = {}
        errors = [type(exc).__name__ + ": " + str(exc)]
    results.append({"id": case["id"], "pass": not errors, "errors": errors})
failed = [row for row in results if not row["pass"]]
shutil.rmtree(OUT / "holdout_tmp", ignore_errors=True)
destination = OUT / "holdout_rerun.json"
destination.write_text(
    json.dumps(
        {
            "digest": digest,
            "passed": len(results) - len(failed),
            "failed": len(failed),
            "blocked_nonlocal_connections": blocked_connections,
            "live_provider_calls": 0,
            "historical_results_path": "artifacts/pr_play_79df3/holdout_results.jsonl",
            "historical_results_rewritten": False,
            "results": results,
        },
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps({
    "passed": len(results) - len(failed),
    "failed": len(failed),
    "blocked_nonlocal_connections": len(blocked_connections),
    "failures": [{"id": row["id"], "errors": row["errors"]} for row in failed],
}, indent=2))
raise SystemExit(1 if failed or blocked_connections else 0)
