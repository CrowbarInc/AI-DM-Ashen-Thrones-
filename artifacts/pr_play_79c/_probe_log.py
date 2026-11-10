import json
from pathlib import Path
lines = Path("artifacts/pr_play_79c/browser_data/session_log.jsonl").read_text(encoding="utf-8").splitlines()
print("lines", len(lines))
last = json.loads(lines[-1])
print(last.keys())
text = json.dumps(last)
for key in ("player_facing_text", "expression", "bounded", "owner", "purpose"):
    print("---", key, text.lower().find(key))
print(text[:2500])
