"""Re-run the frozen 79D-F3 holdout into this cycle's evidence directory.

Does not write artifacts/pr_play_79df3/holdout_results.jsonl.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ.pop("ASHEN_DISABLE_PROVIDER_CALLS", None)

from tests.helpers.storage_isolation import install

install(Path(tempfile.mkdtemp(prefix="at-opt-02-holdout-")))

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
destination = OUT / "holdout_rerun.json"
destination.write_text(json.dumps({"digest": digest, "results": results}, indent=2), encoding="utf-8")
failed = [row for row in results if not row["pass"]]
print(json.dumps({"passed": len(results) - len(failed), "failed": len(failed), "failures": failed}, indent=2))
raise SystemExit(1 if failed else 0)
