import json
from pathlib import Path

d = json.loads(Path("artifacts/pr_play_79c/live_http.json").read_text(encoding="utf-8"))
print("SEED", d["integrated"]["seed"])
print("RESUME", d["integrated"]["resume"])
for i, t in enumerate(d["integrated"]["transcript"]):
    text = (t.get("player_facing_text") or "").replace("\n", " ")
    print("---", i, t.get("input"))
    print(
        "adopt", t.get("dialogue_adopted"),
        "pub", t.get("dialogue_published"),
        "repl", t.get("dialogue_replaced"),
        "narrA", t.get("narration_adopted"),
        "narrP", t.get("narration_published"),
        "clar", t.get("clarification"),
        "primary", t.get("primary_narration"),
        "ms", t.get("elapsed_ms"),
    )
    print("SPEECH", t.get("dialogue_text"))
    print("FACE", text[:700])
    print("REASONS", t.get("dialogue_reasons"), "NARR", t.get("narration_reasons"))
