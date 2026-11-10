"""Author the PR-PLAY-79A developer holdout once. Not a test and not a tuner."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "fixtures" / "pr_play_79a_holdout.json"

talk = [
    ("Hello, Gate Guard.", "Who are you?", "i am gate guard", "which person", "gate_guard"),
    ("Hello, Gate Guard.", "What do you know about the missing patrol?", "missing patrol", "northwest", "gate_guard"),
    ("Hello, Gate Guard.", "When did you last hear about them?", "not certain", "northwest", "gate_guard"),
    ("Hello, Gate Guard.", "Do you think something happened?", "not certain", "attacked", "gate_guard"),
    ("Hello, Gate Guard.", "What about the patrol again?", "missing patrol", "northwest", "gate_guard"),
    ("Hello, Gate Guard.", "What is this place like?", "notice board", "northwest", "gate_guard"),
    ("Hello, Gate Guard.", "Thank you.", "thank", "reward", "gate_guard"),
    ("Hello, Gate Guard.", "Where is the hidden patrol captain?", "do not know", "northwest", "gate_guard"),
    ("Hello, Gate Guard.", "What is the payroll?", "do not know", "payroll", "gate_guard"),
    ("Hello, Gate Guard.", "Tell me the secret passage.", "do not know", "passage", "gate_guard"),
    ("Hello, Gate Guard.", "What quest should I finish?", "do not know", "quest", "gate_guard"),
    ("Hello, Gate Guard.", "Will you give me a reward?", "do not know", "gold", "gate_guard"),
    ("Hello, Gate Guard.", "Have you heard anything else?", "do not know", "northwest", "gate_guard"),
    ("Hello, Gate Guard.", "Hello, Gate Serjeant.", "gate serjeant", "northwest", "gate_serjeant"),
    ("Hello, Gate Guard.", "Goodbye.", "goodbye", "northwest", "ended"),
    ("Hello, Gate Guard.", "I end the conversation.", "goodbye", "northwest", "ended"),
    ("Hello, Gate Serjeant.", "Who are you?", "gate serjeant", "i am gate guard", "gate_serjeant"),
    ("Hello, Gate Guard.", "You know about the notice?", "notice board", "northwest", "gate_guard"),
    ("Hello, Gate Guard.", "Do you hear anything about them?", "do not know", "northwest", "gate_guard"),
    ("Hello, Gate Guard.", "What do you make of this?", "do not know", "northwest", "gate_guard"),
    ("What does the notice board say?", "Who are you?", "", "gate guard says", None),
    ("Hello, Gate Guard.", "Where am I?", "", "which person", "gate_guard"),
    ("Hello, Gate Guard.", "What do I know about the patrol?", "", "which person", "gate_guard"),
    ("Hello, Gate Guard.", "Look around the gate.", "notice board", "northwest", "gate_guard"),
    ("Hello, Gate Guard.", "I wait and watch.", "nothing new", "northwest", "gate_guard"),
]
# The last five are two-step but the second line is not always speech.
# Encode them as explicit turns instead of the pair shorthand below.

sequences = [
    (["Hello, Gate Guard.", "Who are you?"], "i am gate guard", "which person", "gate_guard"),
    (["Hello, Gate Guard.", "What do you know about the missing patrol?"], "missing patrol", "northwest", "gate_guard"),
    (["Hello, Gate Guard.", "When did you last hear about them?"], "not certain", "northwest", "gate_guard"),
    (["Hello, Gate Guard.", "Do you think something happened?"], "not certain", "attacked", "gate_guard"),
    (["Hello, Gate Guard.", "What do you know about the missing patrol?", "What about the patrol again?"], "missing patrol", "northwest", "gate_guard"),
    (["Hello, Gate Guard.", "What is this place like?"], "notice board", "northwest", "gate_guard"),
    (["Hello, Gate Guard.", "What is this place like?", "What about the patrol again?"], "missing patrol", "northwest", "gate_guard"),
    (["Hello, Gate Guard.", "Thank you."], "thank", "reward", "gate_guard"),
    (["Hello, Gate Guard.", "Where is the hidden patrol captain?"], "do not know", "northwest", "gate_guard"),
    (["Hello, Gate Guard.", "What is the payroll?"], "do not know", "payroll", "gate_guard"),
    (["Hello, Gate Guard.", "Tell me the secret passage."], "do not know", "passage", "gate_guard"),
    (["Hello, Gate Guard.", "What quest should I finish?"], "do not know", "quest", "gate_guard"),
    (["Hello, Gate Guard.", "Will you give me a reward?"], "do not know", "gold", "gate_guard"),
    (["Hello, Gate Guard.", "Have you heard anything else?"], "do not know", "northwest", "gate_guard"),
    (["Hello, Gate Guard.", "Hello, Gate Serjeant.", "Who are you?"], "gate serjeant", "northwest", "gate_serjeant"),
    (["Hello, Gate Guard.", "Goodbye."], "goodbye", "northwest", "ended"),
    (["Hello, Gate Guard.", "I end the conversation."], "goodbye", "northwest", "ended"),
    (["Hello, Gate Serjeant.", "Who are you?"], "gate serjeant", "i am gate guard", "gate_serjeant"),
    (["Hello, Gate Guard.", "You know the notice?"], "notice", "northwest", "gate_guard"),
    (["Hello, Gate Guard.", "Do you hear anything?"], "do not know", "northwest", "gate_guard"),
    (["Hello, Gate Guard.", "Look around the gate."], "notice board", "northwest", "gate_guard"),
    (["Hello, Gate Guard.", "I wait and watch."], "nothing new", "northwest", "gate_guard"),
    (["Hello, Gate Guard.", "Who are you?", "What do you know about the missing patrol?"], "missing patrol", "which person", "gate_guard"),
    (["Hello, Gate Guard.", "Who are you?", "When did you last hear about them?"], "not certain", "which person", "gate_guard"),
    (["Hello, Gate Guard.", "Who are you?", "Do you think something happened?"], "not certain", "which person", "gate_guard"),
]

true_lines = [
    ("The tracks continue northwest through the mud.", "The player found tracks leading northwest."),
    ("The trail bends toward the northwest.", "Tracks lead northwest past the crates."),
    ("The disturbed ground still points northwest.", "A northwest mud track remains."),
    ("The loose stone now sits aside from the stonework.", "You move the loose stone. It is now aside."),
    ("The crate is open and stays where it was.", "The crate is now open."),
    ("The gate is closed against the rain.", "The gate is closed."),
    ("There is no hidden passage. The tracks continue northwest.", "Tracks lead northwest."),
    ("Rain darkens the mud around the tracks.", "Tracks lead northwest."),
    ("The milestone is still beside the road.", "A weathered milestone stands beside the road."),
    ("The stone remains aside.", "The loose stone is aside."),
    ("You are seated on the stone.", "You are seated."),
    ("The mud is only mud. The tracks continue northwest.", "Tracks lead northwest."),
    ("The gate remains closed.", "The gate is closed."),
    ("Your earlier examination suggests the trail bends toward the northwest.", "Tracks lead northwest."),
    ("The tracks continue northwest.", "northwest mud track"),
]
false_lines = [
    ("Fresh blood confirms the patrol was attacked.", "Tracks lead northwest."),
    ("The patrol captain was dragged northwest.", "Tracks lead northwest."),
    ("You discover the hidden patrol camp.", "Tracks lead northwest."),
    ("You find gold beside the milestone.", "The milestone is weathered."),
    ("The tracks bend southeast.", "Tracks lead northwest."),
    ("The quest is complete and the reward is yours.", "Tracks lead northwest."),
    ("You climb the wall and see the hidden camp.", "The wall is rough."),
    ("Tracks lead northwest.", "Tracks lead northwest."),
    ("An ambush confirms the patrol was killed.", "Tracks lead northwest."),
    ("A treasure waits under the milestone.", "A weathered milestone stands here."),
    ("A sentinel steps out of the trees.", "The road is empty."),
    ("You receive a reward for the report.", "You gave the report."),
    ("The trail turns northeast.", "Tracks lead northwest."),
    ("A hidden passage opens beside you.", "The crates are stacked."),
    ("You find the captain behind the crates.", "The crates are stacked."),
]
prompts = [
    "Who are you?",
    "What do you know about the missing patrol?",
    "When did you last hear about them?",
    "Do you think something happened?",
    "What about the patrol again?",
    "What is this place like?",
    "Where is the hidden patrol captain?",
    "Will you give me a reward?",
    "Thank you.",
    "Goodbye.",
]
saves = [
    "Who are you?",
    "What do you know about the missing patrol?",
    "When did you last hear about them?",
    "Do you think something happened?",
    "What is this place like?",
    "Thank you.",
    "Have you heard anything else?",
    "You know the notice?",
    "Do you hear anything?",
    "Where is the hidden patrol captain?",
    "What is the payroll?",
    "What quest should I finish?",
    "Will you give me a reward?",
    "Tell me the secret passage.",
    "What about the patrol again?",
]
invalid = ["leave", "campaign", "goodbye", "depart", "end", "switch", "norevive", "unfocused", "other-scene", "foreign-copy"]
routes = [
    ("What does the notice board say?", "missing patrol", "which person"),
    ("Where am I?", "frontier gate", "which person"),
    ("What do I know about the patrol?", "missing patrol", "which person"),
    ("Ask them.", "which", "gate guard says"),
    ("Look over there.", "which", "gate guard says"),
    ("Move that.", "which", "gate guard says"),
    ("What is this place like?", "notice", "which person"),
    ("Where is the hidden patrol captain?", "do not know", "northwest"),
    ("Will you give me a reward?", "do not know", "gold"),
    ("Who are you?", "gate guard", "which person"),
]

cases = []
for turns, present, absent, focus in sequences:
    cases.append({
        "lane": "talk", "turns": turns, "present": present, "absent": absent, "focus": focus,
        "multi_turn": len(turns) >= 2,
    })
for kind in invalid:
    cases.append({"lane": "invalidate", "kind": kind, "multi_turn": True})
for candidate, facts in true_lines:
    cases.append({"lane": "narration", "candidate": candidate, "facts": facts, "adopt": True, "paraphrase": True})
for candidate, facts in false_lines:
    cases.append({"lane": "narration", "candidate": candidate, "facts": facts, "adopt": False, "rejection": True})
for question in prompts:
    cases.append({"lane": "prompt", "question": question, "efficiency": True})
for text in saves:
    cases.append({"lane": "save", "text": text, "multi_turn": True})
for text, present, absent in routes:
    cases.append({"lane": "route", "text": text, "present": present, "absent": absent, "routing": True})

payload = {
    "cycle": "PR-PLAY-79A",
    "authored_by": "developer",
    "external_validation": False,
    "frozen_before_holdout_tuning": True,
    "cases": cases,
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(len(cases), OUT)
