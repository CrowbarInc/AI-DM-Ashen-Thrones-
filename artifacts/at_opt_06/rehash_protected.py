"""Re-hash the PR-PLAY-79D-F3 protected file set. Read-only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "artifacts" / "pr_play_79df3" / "protected_entry.json"
OUT = Path(__file__).resolve().parent / "protected_rehash.json"


def main() -> int:
    entry = json.loads(ENTRY.read_text(encoding="utf-8"))
    changed = []
    missing = []
    unchanged = 0
    for row in entry["files"]:
        path = ROOT / str(row["path"])
        if not path.is_file():
            missing.append(str(row["path"]).replace("\\", "/"))
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest == row["sha256"]:
            unchanged += 1
        else:
            changed.append(str(row["path"]).replace("\\", "/"))
    report = {
        "source": "artifacts/pr_play_79df3/protected_entry.json",
        "count": len(entry["files"]),
        "unchanged": unchanged,
        "changed": changed,
        "missing": missing,
        "live_provider_calls": 0,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"count": report["count"], "unchanged": unchanged, "changed": len(changed), "missing": len(missing)}))
    return 1 if changed or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
