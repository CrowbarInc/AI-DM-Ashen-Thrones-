"""Two normal TCP campaigns. Creation uses the public campaign APIs."""
import os
os.environ["PR73_STORAGE"] = "http_data"
os.environ["PR73_NETWORK"] = "http_network.jsonl"
import json
import statistics
from runtime import OUT, snapshot, storage
from artifacts.pr_play_67.http_harness import server
from tests.test_pr_play_71_lifecycle import byid


def main():
    rows = []
    summaries = []
    with server() as request:
        def call(path, payload=None):
            before = snapshot()
            row = request(path, payload)
            row.update(authority_before=before, authority_after=snapshot())
            rows.append(row)
            (OUT / "http_traces.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
            assert row["status"] == 200 and not row["hidden_exposures"], row
            return row["body"]

        def chat(text):
            return call("/api/chat", {"text": text})

        def act(aid):
            action = byid(aid)
            return call("/api/action", {"action_type": "exploration", "intent": action["label"], "exploration_action": {"id": aid, "type": "custom", "label": action["label"]}})

        def unchanged(before, after):
            return before["world"]["world_state"]["flags"] == after["world"]["world_state"]["flags"] and before["session"].get("discovered_clues") == after["session"].get("discovered_clues") and before["session"]["active_scene_id"] == after["session"]["active_scene_id"]

        for branch in ("survey", "report"):
            identity = call("/api/new_campaign", {})["campaign_run_id"]
            call("/api/start_campaign", {})
            chat("I examine the notice board.")
            chat("I follow the missing patrol rumor.")
            chat("I examine the weathered milestone.")
            act("patrol_" + branch)
            if branch == "report":
                chat("I return to Cinderwatch Gate.")
            follow = "Please record my survey." if branch == "survey" else "Please give the watch my patrol report."
            chat(follow)
            flag = "patrol_survey_recorded" if branch == "survey" else "patrol_guards_warned"
            assert storage.load_world()["world_state"]["flags"][flag]
            record = {}
            if branch == "survey":
                before = snapshot()
                physical = chat("I want to climb onto the broken stonework to get a better view of the road.")
                record["physical"] = physical["gm_output"]["player_facing_text"]
                assert "not established" in record["physical"]
                assert unchanged(before, snapshot()) and snapshot() == before
                observation = chat("From up here, can I see anything farther down the road?")
                record["observation"] = observation["gm_output"]["player_facing_text"]
                assert "Nothing farther is established." in record["observation"]
                assert "No elevated position is established" in record["observation"]
                assert unchanged(before, snapshot())
            else:
                before = snapshot()
                social = chat("I want to persuade the watch to take my warning more seriously.")
                record["social"] = social["gm_output"]["player_facing_text"]
                assert "No new order or compliance is established" in record["social"]
                assert "DC" in record["social"]
                assert unchanged(before, snapshot())
                manipulation = chat("I want to move some loose stones aside and check underneath.")
                record["manipulation"] = manipulation["gm_output"]["player_facing_text"]
                assert "not established" in record["manipulation"]
                ambiguous = chat("Ask them.")
                record["ambiguous"] = ambiguous["gm_output"]["player_facing_text"]
                assert "?" in record["ambiguous"]
                assert snapshot()["world"]["world_state"]["flags"] == before["world"]["world_state"]["flags"]
            quiet = snapshot()
            readonly = chat("What can I see from here?" if branch == "survey" else "Have the guards done anything?")
            record["read_only"] = readonly["gm_output"]["player_facing_text"]
            assert snapshot() == quiet
            if branch == "survey":
                blocked = chat("I want to find a secret passage beneath the milestone.")
                record["unsupported"] = blocked["gm_output"]["player_facing_text"]
                assert "has been created" in record["unsupported"]
                assert snapshot() == quiet
            saved = call("/api/snapshots", {"label": "PR73 HTTP " + branch})["snapshot"]["id"]
            transcript = call("/api/log")
            call("/api/snapshots/load", {"snapshot_id": saved})
            assert call("/api/log") == transcript
            resumed = snapshot()
            if branch == "survey":
                again = chat("I look farther down the road once more.")
                record["reference"] = again["gm_output"]["player_facing_text"]
                assert "Nothing farther is established." in record["reference"]
                assert storage.load_session().get("discovered_clues") == resumed["session"].get("discovered_clues")
            else:
                again = chat("I appeal to the watch again about the warning.")
                record["reference"] = again["gm_output"]["player_facing_text"]
                assert "No new order or compliance is established" in record["reference"]
                assert storage.load_world()["world_state"]["flags"] == resumed["world"]["world_state"]["flags"]
            summaries.append({"branch": branch, "identity": identity, "snapshot_id": saved, "flag": flag, "texts": record, "resumed": True})
    durations = [row["http_ms"] for row in rows]
    summary = {
        "campaigns": summaries,
        "requests": len(rows),
        "mean_http_ms": statistics.mean(durations),
        "median_http_ms": statistics.median(durations),
        "max_http_ms": max(durations),
        "provider_requests": 0,
        "provider_tokens": 0,
        "hidden_exposures": sum(bool(row["hidden_exposures"]) for row in rows),
    }
    (OUT / "http_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
