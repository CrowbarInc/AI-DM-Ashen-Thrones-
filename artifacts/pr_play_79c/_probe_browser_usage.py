import json
from pathlib import Path
path = Path("artifacts/pr_play_79c/browser_data/provider_usage.jsonl")
rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
done = [r for r in rows if r.get("event") == "completed" and r.get("sent")]
print("rows", len(rows), "sent", len(done))
for r in done:
    print(r.get("purpose"), r.get("total_tokens"), r.get("input_tokens"), r.get("output_tokens"), r.get("latency_ms"))
print("tokens", sum(int(r.get("total_tokens") or 0) for r in done))
