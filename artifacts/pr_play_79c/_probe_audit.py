import json
from pathlib import Path
session = json.loads(Path("artifacts/pr_play_79c/browser_data/session.json").read_text(encoding="utf-8"))
print("top last_background", session.get("last_background_expression"))
print("top last_publication", json.dumps(session.get("last_publication"), indent=2)[:1500])
print("top last_narration", session.get("last_narration"))
