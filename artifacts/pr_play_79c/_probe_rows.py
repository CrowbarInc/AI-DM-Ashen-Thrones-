import json
from pathlib import Path
path = Path("artifacts/pr_play_79c/browser_data/provider_usage.jsonl")
rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
print("rows", len(rows))
for row in rows:
    print({k: row.get(k) for k in ("event", "purpose", "sent", "refusal", "error", "total_tokens", "owner")})
session = json.loads(Path("artifacts/pr_play_79c/browser_data/session.json").read_text(encoding="utf-8"))
print("has last_background", "last_background_expression" in session)
print("keys sample", [k for k in session if "express" in k or "narrat" in k or "public" in k])
