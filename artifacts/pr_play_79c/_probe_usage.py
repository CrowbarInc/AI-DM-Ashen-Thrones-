import json
from pathlib import Path

path = Path("artifacts/pr_play_79c/browser_data/provider_usage.jsonl")
if not path.exists():
    # find the usage file
    hits = list(Path("artifacts/pr_play_79c/browser_data").rglob("*usage*"))
    print("files", hits)
else:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    done = [r for r in rows if r.get("event") == "completed" and r.get("sent")]
    print("path", path)
    print("completed", len(done), "tokens", sum(int(r.get("total_tokens") or 0) for r in done))
