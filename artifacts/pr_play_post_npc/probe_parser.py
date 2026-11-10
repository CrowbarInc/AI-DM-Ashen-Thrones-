import json
from pathlib import Path

from game.intent_parser import parse_freeform_to_action
from game.referenced_surface import classify_referenced_surface, content_tokens

raw = json.loads(Path("data/scenes/frontier_gate.json").read_text(encoding="utf-8"))
scene = raw["scene"] if isinstance(raw.get("scene"), dict) else raw
env = {"scene": scene}
texts = [
    "I walk over to the notice board and put a hand on the frame.",
    "Read me the missing-patrol notice, not the tax lines.",
    "I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording.",
    "What did that notice say about where the patrol was last seen?",
    "Could you repeat that?",
    "What did the captain just say?",
    "Tell me the warning again.",
    "You mentioned the patrol. What have you heard?",
    "I follow the missing patrol rumor toward the northwest track.",
    "Leave for the old milestone.",
    "I examine the notice board.",
    "Read the notice.",
    "Ask the captain about the notice.",
]
sample = "me the missing-patrol notice, not the tax lines"
print("TOKENS", content_tokens(sample))
print("CLASS", classify_referenced_surface(texts[1], scene, explicit_target=sample))
print("---")
for text in texts:
    act = parse_freeform_to_action(text, env)
    if act is None:
        print("NONE |", text)
        continue
    meta = act.get("metadata") or {}
    print(
        act.get("type"),
        act.get("id"),
        act.get("target_id"),
        meta.get("parser_lane"),
        "|",
        text,
    )
