import json
from pathlib import Path

p = json.loads(Path("artifacts/pr_play_79a/live_http.json").read_text(encoding="utf-8"))
for name in ("conversation", "narration"):
    print("==", name)
    for turn in p[name]["transcript"]:
        if turn.get("input") == "[start_campaign]":
            continue
        slot = (turn.get("after") or {}).get("interlocutor") or {}
        fresh = slot.get("last_player_utterance") == turn.get("input")
        shown = turn.get("player_facing_text") or ""
        dialogue = fresh and turn.get("dialogue_adopted") and "not available" not in shown.casefold() and "which person" not in shown.casefold()
        narration = turn.get("narration_text") and turn.get("narration_text") == shown
        print(fresh, "DLG" if dialogue else "   ", "NAR" if narration else "   ", turn.get("input"), "|", shown[:140].replace("\n", " "))
