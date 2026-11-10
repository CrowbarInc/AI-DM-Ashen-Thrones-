"""Real TCP gameplay: normal creation, branching, typed chat, save and resume."""
import os
os.environ["PR72V_STORAGE"]="http_data"
os.environ["PR72V_NETWORK"]="http_network.jsonl"
import copy
import json
import statistics
import time
from runtime import api, storage, OUT, STAGES, snapshot
from artifacts.pr_play_67.http_harness import server
from tests.test_pr_play_71_lifecycle import byid


def main():
    rows = []; summaries = []; saves = {}
    with server() as request:
        def call(path, payload=None):
            before = snapshot(); stages = {}; token = STAGES.set(stages)
            try: row = request(path, payload)
            finally: STAGES.reset(token)
            capture = json.loads((OUT / "http_network.jsonl").read_text().splitlines()[-1])
            row.update(authority_before=before, authority_after=snapshot(), stages=capture["stages"])
            # ContextVars do not cross the TCP boundary; interpretation and engine
            # outcome are retained from the actual committed turn log instead.
            if path == "/api/chat":
                from game.conversational_orchestration import deterministic_conversational_decision
                scene = api.load_active_scene()
                from game.player_initiative import decide
                d = decide(payload["text"], scene=scene, world=before["world"], session=before["session"])
                row["interpretation_replay"] = d.to_public_dict() if d else None
                row["authoritative_log"] = storage.load_log()[-1]
            rows.append(row)
            (OUT / "http_traces.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
            assert row["status"] == 200 and not row["hidden_exposures"], row
            return row["body"]
        def chat(text): return call("/api/chat", {"text": text})
        def act(aid):
            a = byid(aid)
            return call("/api/action", {"action_type": "exploration", "intent": a["label"], "exploration_action": {"id": aid, "type": "custom", "label": a["label"]}})
        for branch in ("survey", "report"):
            identity = call("/api/new_campaign", {})["campaign_run_id"]
            call("/api/start_campaign", {})
            chat("I examine the notice board.")
            chat("I follow the missing patrol rumor.")
            chat("I examine the weathered milestone.")
            act("patrol_" + branch)
            if branch == "report": chat("I return to Cinderwatch Gate.")
            follow_text = "Please record my survey." if branch == "survey" else "I want to give the watch my patrol report."
            followed = chat(follow_text)
            flag = "patrol_survey_recorded" if branch == "survey" else "patrol_guards_warned"
            assert storage.load_world()["world_state"]["flags"][flag]
            investigation = "May I examine where the footprints disappear?" if branch == "survey" else "Can I speak to the watch about the missing patrol again?"
            chat(investigation)
            if branch == "survey":
                chat("Examine the mud prints.")
                chat("Look at the tracks again.")
                repeat = storage.load_log()[-1]["resolution"]
                assert repeat["kind"] == "already_searched" and repeat["success"] is True
                assert not repeat.get("discovered_clues") and not repeat.get("world_updates")
            if branch == "report":
                chat("I ask the Gate Serjeant about the patrol route.")
                resolved = storage.load_log()[-1]["resolution"]
                assert not str(resolved.get("kind", "")).startswith("conversational_")
            before = snapshot()
            answer = chat("What have I actually learned about the trail?" if branch == "survey" else "I want to check whether the guards have acted on my warning.")
            assert snapshot() == before
            for inquiry in ["Have the guards searched?", "Did I record the survey?", "Search the hidden camp."]:
                chat(inquiry)
                assert snapshot() == before
            chat("I want to follow the tracks all the way to whoever left them." if branch == "survey" else "I want the guards to send a patrol after the missing soldiers immediately.")
            assert snapshot() == before
            chat("Ask them about it.")
            assert snapshot() == before
            saved = call("/api/snapshots", {"label": "PR72 HTTP " + branch})["snapshot"]["id"]
            transcript = call("/api/log")
            call("/api/snapshots/load", {"snapshot_id": saved})
            assert call("/api/log") == transcript
            resumed = snapshot()
            chat("Who have I told about this?")
            assert snapshot() == resumed
            if branch == "survey":
                chat("Examine the tracks once more.")
                repeat = storage.load_log()[-1]["resolution"]
                assert repeat["kind"] == "already_searched" and not repeat.get("discovered_clues")
            else:
                chat("I ask the Gate Serjeant about the patrol route.")
            chat("I return to Cinderwatch Gate." if branch == "survey" else "Read the notice board again.")
            saves[branch] = (saved, identity)
            summaries.append(dict(branch=branch, identity=identity, snapshot_id=saved, followup_flag=flag, information=answer["gm_output"]["player_facing_text"], resumed=True, natural_followup=True, transcript_restored=True))
        for branch, (saved, identity) in saves.items():
            call("/api/snapshots/load", {"snapshot_id": saved})
            assert storage.load_session()["campaign_run_id"] == identity
    durations = [r["http_ms"] for r in rows]
    summary = dict(campaigns=summaries, requests=len(rows), mean_http_ms=statistics.mean(durations), median_http_ms=statistics.median(durations), max_http_ms=max(durations), provider_requests=0, provider_tokens=0, hidden_exposures=sum(bool(r["hidden_exposures"]) for r in rows), stage_timings="Server function durations captured through ContextVar middleware; HTTP total measured separately. Replay interpretation is labeled separately.")
    (OUT / "http_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
