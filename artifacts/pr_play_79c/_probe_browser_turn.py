import json
from pathlib import Path

session = json.loads(Path("artifacts/pr_play_79c/browser_data/session.json").read_text(encoding="utf-8"))
audit = session.get("last_background_expression") or {}
attempt = audit.get("attempt") if isinstance(audit.get("attempt"), dict) else {}
print("adopted", audit.get("adopted"))
print("reason", audit.get("reason"))
print("validation", audit.get("validation"))
print("attempt", attempt.get("text"))
print("operation", attempt.get("operation") or audit.get("operation"))
pub = session.get("last_publication") or {}
print("publication_owner", pub.get("owner"))
print("dialogue_published", pub.get("dialogue_published"))
print("narration", session.get("last_narration"))
rows = [json.loads(line) for line in Path("artifacts/pr_play_79c/browser_data/provider_usage.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
done = [r for r in rows if r.get("event") == "completed" and r.get("sent")]
print("completed", len(done))
for r in done:
    print(r.get("purpose"), r.get("total_tokens"), r.get("latency_ms") or r.get("elapsed_ms"), list(r)[:12])
