import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
cycles = {
    "79": root / "artifacts/pr_play_79/live_data/session_log.jsonl",
    "79A": root / "artifacts/pr_play_79a/live_data/session_log.jsonl",
    "79B": root / "artifacts/pr_play_79b/live_data/session_log.jsonl",
    "79C": root / "artifacts/pr_play_79c/live_data/session_log.jsonl",
}
for name, path in cycles.items():
    print("==", name)
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        text = str(row.get("player_input") or "")[:90]
        stamp = str(row.get("timestamp") or "")
        gm = row.get("gm_output") if isinstance(row.get("gm_output"), dict) else {}
        notes = str(gm.get("debug_notes") or "")
        meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
        route = meta.get("model_route_purpose") or meta.get("model_route_family")
        provider = meta.get("provider_call") if isinstance(meta.get("provider_call"), dict) else {}
        incoming = provider.get("input_tokens")
        if incoming or "call_gpt" in notes or route:
            print(index, stamp, incoming, route, text)
