import hashlib
import json
from pathlib import Path

root = Path(".")
prior = json.loads(Path("artifacts/pr_play_79b/protected_before.json").read_text(encoding="utf-8"))
rows = []
mismatches = []
missing = []
for item in prior["files"]:
    path = root / item["path"]
    if not path.exists():
        missing.append(item["path"])
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    same = digest == item["sha256"]
    rows.append({"path": item["path"], "sha256": digest, "bytes": path.stat().st_size, "matches_pr_play_79b": same})
    if not same:
        mismatches.append(item["path"])
report = {
    "count": len(rows),
    "prior_count": prior["count"],
    "preserved": len(rows) - len(mismatches),
    "mismatches": mismatches,
    "missing": missing,
    "files": rows,
}
Path("artifacts/pr_play_79c/protected_after.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"preserved": report["preserved"], "count": report["count"], "mismatches": mismatches, "missing": missing}))
