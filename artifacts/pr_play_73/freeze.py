"""Write the frozen holdout file and its hash. Does not execute cases."""
import hashlib
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
from holdout_cases import CASES

rows = []
for item in CASES:
    (cid, group, branch, text, category, family, decision, reason, state_same, pub_any, pub_none, persist) = item
    rows.append({
        "id": cid, "group": group, "branch": branch, "text": text,
        "expected": {
            "gp_category": category, "gp_family": family, "decision": decision,
            "reason": reason, "state_unchanged": state_same,
            "publication_any": pub_any, "publication_none": pub_none, "persist": persist,
            "flags_unchanged": True, "clues_unchanged": True, "scene_unchanged": True,
        },
    })
payload = json.dumps(rows, indent=2).encode()
target = OUT / "frozen_holdout.json"
target.write_bytes(payload)
digest = hashlib.sha256(payload).hexdigest()
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, text=True).strip()
manifest = {
    "authorship": "developer-authored; not independent external validation",
    "cases": len(rows),
    "sha256": digest,
    "bytes": len(payload),
    "branch": branch,
    "head": head,
    "note": "Frozen before the single holdout execution. Do not edit frozen_holdout.json to repair failures.",
}
(OUT / "frozen_holdout_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))
