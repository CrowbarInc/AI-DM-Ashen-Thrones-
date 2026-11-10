import json
from pathlib import Path
lines = Path("artifacts/pr_play_79c/browser_data/session_log.jsonl").read_text(encoding="utf-8").splitlines()
print("log_entries", len(lines))
for line in lines:
    row = json.loads(line)
    player = row.get("player_input")
    gm = ((row.get("gm_output") or {}).get("player_facing_text") or "").replace("\n", " ")
    meta = ((row.get("resolution") or {}).get("metadata") or {})
    integ = meta.get("integrated_play") or {}
    print("---")
    print("IN", player)
    print("FACE", gm[:240])
    print("live", integ.get("live_dialogue"), "published", integ.get("dialogue_published"), "narr", integ.get("live_narration"), "ms", integ.get("latency_ms"))
