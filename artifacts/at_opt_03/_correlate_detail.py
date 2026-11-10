import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
wanted = {
    "79": {1, 13, 17},
    "79A": {1, 9},
    "79B": {1},
    "79C": {1},
}
paths = {
    "79": root / "artifacts/pr_play_79/live_data/session_log.jsonl",
    "79A": root / "artifacts/pr_play_79a/live_data/session_log.jsonl",
    "79B": root / "artifacts/pr_play_79b/live_data/session_log.jsonl",
    "79C": root / "artifacts/pr_play_79c/live_data/session_log.jsonl",
}
for name, path in paths.items():
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for index in sorted(wanted[name]):
        row = lines[index - 1]
        resolution = row.get("resolution") if isinstance(row.get("resolution"), dict) else {}
        gm = row.get("gm_output") if isinstance(row.get("gm_output"), dict) else {}
        visible = str(row.get("player_facing_text") or gm.get("player_facing_text") or "")[:160]
        print(json.dumps({
            "cycle": name,
            "index": index,
            "player": str(row.get("player_input") or "")[:120],
            "kind": resolution.get("kind"),
            "scene": (resolution.get("metadata") or {}).get("scene_id") if isinstance(resolution.get("metadata"), dict) else None,
            "tags": (gm.get("tags") or [])[:8],
            "visible": visible,
        }, ensure_ascii=False))
