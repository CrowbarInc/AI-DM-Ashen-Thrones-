"""Create the two branch starting states used by the frozen holdout. Does not score cases."""
import os
os.environ["PR73_STORAGE"] = "holdout_data"
os.environ["PR73_NETWORK"] = "freeze_network.jsonl"
import hashlib
import json
from runtime import OUT, ROOT, api, snapshot, storage
from artifacts.pr_play_67.http_harness import server
from tests.test_pr_play_71_lifecycle import byid

with server() as request:
    def call(path, payload=None):
        row = request(path, payload)
        assert row["status"] == 200, row
        return row["body"]

    def chat(text):
        return call("/api/chat", {"text": text})

    states = {}
    slots = {}
    for branch in ("survey", "report"):
        call("/api/new_campaign", {})
        call("/api/start_campaign", {})
        chat("I examine the notice board.")
        chat("I follow the missing patrol rumor.")
        chat("I examine the weathered milestone.")
        action = byid("patrol_" + branch)
        call("/api/action", {"action_type": "exploration", "intent": action["label"], "exploration_action": {"id": action["id"], "type": "custom", "label": action["label"]}})
        if branch == "report":
            chat("I return to Cinderwatch Gate.")
        follow = "Please record my survey." if branch == "survey" else "Please give the watch my patrol report."
        chat(follow)
        flag = "patrol_survey_recorded" if branch == "survey" else "patrol_guards_warned"
        assert storage.load_world()["world_state"]["flags"][flag]
        states[branch] = snapshot()
        slots[branch] = call("/api/snapshots", {"label": "PR73 frozen " + branch})["snapshot"]["id"]

(OUT / "frozen_start_states.json").write_text(json.dumps(states), encoding="utf-8")
(OUT / "holdout_slots.json").write_text(json.dumps(slots), encoding="utf-8")
manifest = json.loads((OUT / "frozen_holdout_manifest.json").read_text(encoding="utf-8"))
manifest["states_sha256"] = hashlib.sha256((OUT / "frozen_start_states.json").read_bytes()).hexdigest()
manifest["slots"] = slots
(OUT / "frozen_holdout_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"slots": slots, "states_sha256": manifest["states_sha256"]}, indent=2))
