"""Author the PR-PLAY-77 frozen holdout once. Do not regenerate it to chase failures."""
import json
from pathlib import Path

cases = []


def add(group, setup, turns, save=False, multi=False, campaign=None):
    case = {"id": f"H{len(cases)+1:03d}", "group": group, "setup": setup, "turns": turns, "save": save, "multi": multi or len(turns) > 1}
    if campaign:
        case["campaign"] = campaign
    cases.append(case)


def one(text, category, fragment, absent=None):
    turn = {"input": text, "category": category, "fragment": fragment}
    if absent:
        turn["absent"] = absent
    return [turn]


# Sequential actions, varied wording.
sequential = [
    ("I open the door and look inside.", "door", "A", "nothing concealed"),
    ("Please open the door, then look inside.", "door", "A", "nothing concealed"),
    ("Let me unlatch the door and check inside.", "door", "A", "nothing concealed"),
    ("I will push the crate aside and look where it was.", "crate", "A", "aside"),
    ("First shift the crate aside; next, inspect it.", "crate", "A", "aside"),
    ("I sit on the bench and stand up.", "bench", "A", "you stand"),
    ("Approach the bench and sit on it.", "bench", "A", "you sit"),
    ("I stand up and approach the bench.", "bench", "A", "beside"),
    ("Lift the cup and place the cup aside.", "cup", "A", "aside"),
    ("I push the crate away from the doorway and check the doorway.", "blocking", "A", "the doorway is clear"),
    ("Open the door and then look inside.", "door", "A", "you open"),
    ("I close the door and look inside.", "open", "A", "nothing concealed"),
    ("Nudge the crate aside, then inspect it.", "crate", "A", "aside"),
    ("I walk over to the bench and sit on the bench.", "bench", "A", "you sit"),
    ("Step back from the bench and stand up.", "beside", "A", "already standing"),
    ("I open the door; look inside.", "door", "A", "nothing concealed"),
    ("Heave the cup and set the cup aside.", "cup", "A", "aside"),
    ("I pull the crate aside and look where it was.", "crate", "A", "aside"),
    ("Please have a seat on the bench and stand up.", "bench", "A", "you stand"),
    ("I approach the notice board and step back from the notice board.", "notice", "A", "step back"),
]
for index, (text, setup, category, fragment) in enumerate(sequential):
    if index < 10:
        add("sequential", setup, [
            {"input": text, "category": category, "fragment": fragment},
            {"input": "Am I standing?", "category": "A", "fragment": "seated" if "sit on it" in text or "sit on the bench and" not in text and "sit on the bench" in text else "standing here"},
        ], save=True, multi=True)
    else:
        add("sequential", setup, one(text, category, fragment))

dependency = [
    ("I open the locked door and look inside.", "locked", "D", "not attempted", "nothing concealed"),
    ("I open the hatch and sit on the bench.", "bench", "E", "not attempted", "you sit"),
    ("I push the crate and open the hatch.", "crate", "A", "not established", None),
    ("Open the door, step through, and look around.", "door", "A", "no passage", "room was created"),
    ("I open the door and climb the milestone.", "door_milestone", "A", "no climbing check", "you reach"),
    ("Push the crate aside, climb the milestone, and look down the road.", "crate_milestone", "A", "not attempted", "hidden road"),
    ("I break the door and look inside.", "door", "C", "not attempted", "you open"),
    ("If the door opens, look inside.", "door", "A", "skipped", "nothing concealed"),
    ("I open the stuck door and look inside.", "hard", "B", "attempt fails", "nothing concealed"),
    ("Move the crate through the wall and look inside.", "crate", "E", "unchanged", None),
    ("I open the guarded door and look inside.", "guarded", "C", "not attempted", "you open"),
    ("I open the door, and if it opens, look inside.", "locked", "D", "not attempted", "nothing concealed"),
    ("I pick up the cup and examine it.", "cup", "D", "not attempted", "raised"),
    ("I climb the milestone and survey the road.", "milestone", "D", "not attempted", "hidden road"),
    ("I push the pillar and look where it was.", "pillar", "E", "not attempted", "aside"),
]
for text, setup, category, fragment, absent in dependency:
    add("dependency", setup, one(text, category, fragment, absent), multi=True)

partial = [
    ("I push the crate aside, climb the milestone, and look down the road.", "crate_milestone", "A", "aside"),
    ("Open the door, step through, and look around.", "door", "A", "you open"),
    ("I lift the cup, climb the milestone, and survey the road.", "cup_milestone", "A", "raised"),
    ("Push the crate away from the doorway, climb the milestone, and look down the road.", "blocking_milestone", "A", "doorway"),
    ("I open the door and climb the milestone.", "door_milestone", "A", "no climbing check"),
    ("I sit on the bench, climb the milestone, and look down the road.", "bench_milestone", "A", "you sit"),
    ("Approach the bench, climb the milestone, and survey the road.", "bench_milestone", "A", "beside"),
    ("I stand up, climb the milestone, and look down the road.", "milestone", "A", "no climbing check"),
    ("Open the door, step through, and peer around.", "door", "A", "no passage"),
    ("I push the loose stone aside and climb the milestone.", "fitting_milestone", "A", "no climbing check"),
    ("Move the crate aside and climb the milestone.", "crate_milestone", "A", "aside"),
    ("I open the door, then step through.", "door", "A", "no passage"),
    ("Lift the cup and climb the milestone.", "cup_milestone", "A", "raised"),
    ("I approach the notice board and climb the milestone.", "notice_milestone", "A", "no climbing check"),
    ("Push the crate farther and climb the milestone.", "crate_milestone", "A", "farther"),
]
for text, setup, category, fragment in partial:
    add("partial", setup, one(text, category, fragment, "hidden road"), multi=True)

conditional = [
    ("If the door opens, look inside.", "door", "A", "skipped"),
    ("If the door is open, look inside.", "open", "A", "nothing concealed"),
    ("If the crate is aside, look where it was.", "crate", "A", "skipped"),
    ("If I am beside the bench, step back from the bench.", "bench", "A", "skipped"),
    ("If I am beside the bench, step back from the bench.", "beside", "A", "step back"),
    ("If I can reach the ledge, try to climb it.", "milestone", "D", "not established"),
    ("If the door opens, then look inside.", "door", "A", "not met"),
    ("If the wooden door opens, check inside.", "open", "A", "nothing concealed"),
    ("If the crate moves, step through.", "crate", "A", "skipped"),
    ("If the door is opened, peer inside.", "door", "A", "skipped"),
]
for text, setup, category, fragment in conditional:
    add("conditional", setup, one(text, category, fragment), multi=True)

independent = [
    ("I open the locked door and stand up.", "locked", "A", "locked"),
    ("I open the locked door and approach the bench.", "locked_bench", "A", "beside"),
    ("I push the pillar and stand up.", "pillar", "A", "cannot be moved"),
    ("I open the hatch and wave to the guard.", "none", "E", "not attempted"),
    ("I stand up and approach the notice board.", "notice", "A", "beside"),
    ("I sit on the bench and wave.", "bench", "A", "you sit"),
    ("The door is locked, so I stand up and approach the bench.", "locked_bench", "A", "beside"),
    ("I open the guarded door and stand up.", "guarded", "C", "not attempted"),
    ("I climb the missing spire and stand up.", "none", "E", "not attempted"),
    ("I stand up and greet the traveler.", "none", "A", "not resolved"),
]
for text, setup, category, fragment in independent:
    add("independent", setup, one(text, category, fragment))

continuity = [
    ("Move the crate aside and inspect it.", "crate", "A", "aside"),
    ("I open the door and close it.", "door", "A", "you close"),
    ("I sit on the bench and stand up.", "bench", "A", "standing"),
    ("I approach the bench and step back from it.", "bench", "A", "step back"),
    ("Push it aside and look where it was.", "crate", "A", "aside"),
    ("I open it and look inside.", "door", "A", "nothing concealed"),
    ("Sit on it and stand up.", "bench", "A", "you stand"),
    ("I lift the cup and place it aside.", "cup", "A", "aside"),
    ("Approach the notice board and read it.", "notice", "A", "beside"),
    ("I push the crate aside and push it farther.", "crate", "A", "farther"),
]
for text, setup, category, fragment in continuity:
    add("continuity", setup, one(text, category, fragment), multi=True)

# Persistence: action, save, question.
persistence = [
    ("I open the door and look inside.", "Is the door still open?", "door", "you open", "is open"),
    ("I sit on the bench and stand up.", "Am I standing?", "bench", "you stand", "standing"),
    ("I push the crate aside and look where it was.", "Where is the crate?", "crate", "aside", "aside"),
    ("I approach the bench and sit on it.", "Am I sitting?", "bench", "you sit", "seated"),
    ("Open the door, step through, and look around.", "Is the door open?", "door", "you open", "is open"),
    ("I push the crate aside, climb the milestone, and look down the road.", "Where is the crate?", "crate_milestone", "aside", "aside"),
    ("I stand up and approach the bench.", "Am I beside the bench?", "bench", "beside", "beside"),
    ("Lift the cup and place the cup aside.", "Where is the cup?", "cup", "aside", "aside"),
    ("I open the locked door and stand up.", "Is the door open?", "locked", "locked", "closed"),
    ("If the door opens, look inside.", "Is the door open?", "door", "skipped", "closed"),
]
for first, second, setup, frag1, frag2 in persistence:
    add("persistence", setup, [
        {"input": first, "category": "A" if "locked" not in first and not first.startswith("If") else ("D" if "locked" in first else "A"), "fragment": frag1},
        {"input": second, "category": "A", "fragment": frag2},
    ], save=True, multi=True)

readonly = [
    ("Is the door open, and what is on the other side?", "door", "A", "nothing was opened"),
    ("Is the door open and what lies beyond?", "open", "A", "nothing was opened"),
    ("Can I move the crate?", "crate", "A", "nothing has been moved"),
    ("Am I sitting, and what is on the other side?", "none", "A", "not seated"),
    ("Is the doorway clear, and what lies beyond?", "none", "D", "no doorway"),
    ("Is the door locked, and what is on the hidden side?", "locked", "A", "locked"),
    ("What is on the other side of the door?", "door", "D", "not established"),
    ("Is the crate still by the wall, and what lies beyond?", "crate", "A", "nothing"),
    ("Can I open the door, and what is on the other side?", "door", "A", "nothing was opened"),
    ("Is the bench here, and what is on the hidden side?", "bench", "D", "not established"),
]
for text, setup, category, fragment in readonly:
    add("readonly", setup, one(text, category, fragment, "you open"))

for text in (
    "I sit on the bench.",
    "Let me sit on the bench.",
    "Please have a seat on the bench.",
    "I will sit on the bench.",
    "I rest on the bench.",
):
    add("isolation", "bench", one(text, "E", "not established", "which seat"), campaign="beta")

publication = [
    ("I push the crate aside, climb the milestone, and look down the road.", "crate_milestone", "A", "not attempted"),
    ("Open the door, step through, and look around.", "door", "A", "not attempted"),
    ("I stand up, approach the bench, sit on the bench, and step back.", "bench", "F", "nothing has been attempted"),
    ("I push the crate and then open it.", "two", "F", "which"),
    ("I open the hidden chest and look inside.", "hidden", "E", "not established"),
]
for text, setup, category, fragment in publication:
    add("publication", setup, one(text, category, fragment, "SENTINEL"))

path = Path(__file__).with_name("frozen_holdout.json")
path.write_text(json.dumps(cases, indent=2), encoding="utf-8")
print(len(cases), path)
print("multi", sum(1 for case in cases if case["multi"]))
print("save", sum(1 for case in cases if case["save"]))
