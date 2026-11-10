"""Frozen developer holdout for PR-PLAY-79D-F2. Run once. Not external validation."""
import hashlib
import json
import os
from pathlib import Path

import pytest

from tests.pr_play_79df2_executor import run_case

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "pr_play_79df2_holdout.json"
ROWS = json.loads(FIXTURE.read_text(encoding="utf-8"))
FIXTURE_SHA = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()


@pytest.mark.parametrize("row", ROWS, ids=[row["id"] for row in ROWS])
def test_frozen_holdout(row, monkeypatch, tmp_path):
    actual = run_case(row, monkeypatch, tmp_path)
    record = {
        "id": row["id"],
        "coverage": row["coverage"],
        "kind": row["kind"],
        "expect": row["expect"],
        "actual": actual,
        "fixture_sha256": FIXTURE_SHA,
    }
    dest = os.environ.get("ASHEN_HOLDOUT_RESULTS")
    if dest:
        path = Path(dest)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    assert actual["pass"], record
