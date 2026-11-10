import json
from pathlib import Path

p = json.loads(Path("artifacts/pr_play_79a/live_http.json").read_text(encoding="utf-8"))
for name in ("conversation", "narration"):
    print("==", name, "stopped", p[name]["stopped"])
    for turn in p[name]["transcript"]:
        said = (turn.get("player_facing_text") or "").replace("\n", " ")[:240]
        usage = turn.get("usage") or {}
        print(
            turn.get("elapsed_ms"),
            "d", turn.get("dialogue_published"),
            "n", turn.get("narration_published"),
            "c", turn.get("clarification"),
            "req", usage.get("requests"),
            "tok", usage.get("tokens"),
        )
        print(" IN", turn.get("input"))
        print(" OUT", said)
        if turn.get("dialogue_reasons"):
            print(" DREASON", turn.get("dialogue_reasons"))
        if turn.get("narration_reasons"):
            print(" NREASON", turn.get("narration_reasons"))
        after = turn.get("after") or {}
        slot = after.get("interlocutor") or {}
        print(" FOCUS", after.get("focus"), slot.get("npc_id"), slot.get("status"))
rows = p.get("provider_rows") or []
from collections import Counter
print("events", Counter(row.get("purpose") or row.get("event") for row in rows))
print("by purpose", Counter((row.get("purpose"), row.get("event"), row.get("sent")) for row in rows))
completed = [row for row in rows if row.get("event") == "completed" and row.get("sent")]
print("completed", len(completed), "tokens", sum(int(row.get("total_tokens") or 0) for row in completed))
for row in completed:
    print(row.get("purpose"), row.get("owner"), row.get("input_tokens"), row.get("output_tokens"), row.get("total_tokens"), row.get("latency_ms"))
