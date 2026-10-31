import json
from pathlib import Path

needles = ["Eldrin", "Verevin", "Velmark", "Durain", "Ash Cowl", "three silver", "3 silver", "copper", "hawk", "milestone", "Rusty Tankard"]
for pid in ["persona_a", "persona_b", "persona_c", "persona_d"]:
    turn = json.loads(Path(pid, "turns", "turn_10.json").read_text(encoding="utf-8"))
    blob = json.dumps({
        "facts": (turn.get("persistence") or {}).get("visible_facts"),
        "clues": (turn.get("persistence") or {}).get("discoverable_clues"),
        "ledger": (turn.get("persistence") or {}).get("ledger_entries"),
        "rejected": (turn.get("persistence") or {}).get("ledger_rejected"),
        "npcs": (turn.get("persistence") or {}).get("npc_ids"),
        "inc": (turn.get("persistence") or {}).get("incidental_entities"),
    })
    hits = [n for n in needles if n.lower() in blob.lower()]
    print(pid, hits)
