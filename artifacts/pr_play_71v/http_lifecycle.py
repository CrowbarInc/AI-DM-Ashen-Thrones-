"""Two real TCP campaigns through the application routes. Provider fixture is offline."""
import copy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pytest
from artifacts.pr_play_67 import http_harness as harness
from game import storage
from tests.test_pr_play_71_lifecycle import byid, configure, flags

OUT = Path(__file__).resolve().parent
ROWS = []
SUMMARIES = []


def texts(body):
    entries = body.get("entries") or []
    return [entry.get("gm_output", {}).get("player_facing_text", "") for entry in entries]


def main():
    started = time.perf_counter()
    with pytest.MonkeyPatch.context() as mp:
        configure(OUT / "http_data", mp)
        with harness.server() as request:
            def call(path, payload=None):
                before = harness.snapshot()
                response = request(path, payload)
                response.update(authority_before=before, authority_after=harness.snapshot())
                ROWS.append(response)
                (OUT / "http_traces.json").write_text(json.dumps(ROWS, indent=2), encoding="utf-8")
                assert response["status"] == 200 and not response["hidden_exposures"], response
                return response["body"]

            saves = {}
            transcripts = {}
            for branch in ("survey", "report"):
                created = call("/api/new_campaign", {})
                identity = created["campaign_run_id"]
                started_body = call("/api/start_campaign", {})
                assert started_body["session"]["campaign_started"] is True
                assert started_body["session"]["active_scene_id"] == "frontier_gate"
                assert started_body["gm_output"]["player_facing_text"]
                for text in (
                    "I examine the notice board.",
                    "I follow the missing patrol rumor.",
                    "I examine the weathered milestone.",
                ):
                    call("/api/chat", {"text": text})
                def act(aid, branch=branch):
                    action = byid(aid)
                    return call("/api/action", {
                        "action_type": "exploration",
                        "intent": action["label"],
                        "exploration_action": {"id": aid, "label": action["label"], "type": "custom"},
                    })
                chosen = act("patrol_" + branch)
                assert chosen["gm_output"]["player_facing_text"] == byid("patrol_" + branch)["consequence"]["text"]
                if branch == "report":
                    call("/api/chat", {"text": "I return to Cinderwatch Gate."})
                follow = "patrol_record_survey" if branch == "survey" else "patrol_warn_watch"
                followed = act(follow)
                assert followed["gm_output"]["player_facing_text"] == byid(follow)["consequence"]["text"]
                committed = copy.deepcopy(flags())
                saved = call("/api/snapshots", {"label": "HTTP " + branch})["snapshot"]["id"]
                call("/api/snapshots/load", {"snapshot_id": saved})
                assert flags() == committed
                log_body = call("/api/log")
                visible = texts(log_body)
                other = byid("patrol_warn_watch" if branch == "survey" else "patrol_record_survey")["consequence"]["text"]
                assert byid(follow)["consequence"]["text"] in visible
                assert other not in visible
                act(follow)
                act("patrol_" + ("report" if branch == "survey" else "survey"))
                assert flags() == committed
                call("/api/chat", {"text": "I examine the mud prints." if branch == "survey" else "I examine the notice board."})
                assert flags() == committed
                saves[branch] = (saved, identity, committed)
                transcripts[branch] = visible
                SUMMARIES.append({
                    "branch": branch,
                    "campaign_run_id": identity,
                    "session_id": storage.load_session()["session_id"],
                    "snapshot_id": saved,
                    "flags": committed,
                    "resumed": True,
                    "continued": True,
                    "transcript_entries": len(visible),
                })
            for branch, (saved, identity, committed) in saves.items():
                call("/api/snapshots/load", {"snapshot_id": saved})
                assert storage.load_session()["campaign_run_id"] == identity and flags() == committed
                restored = texts(call("/api/log"))
                assert restored == transcripts[branch]
            assert SUMMARIES[0]["campaign_run_id"] != SUMMARIES[1]["campaign_run_id"]
    summary = {
        "campaigns": SUMMARIES,
        "requests": len(ROWS),
        "gameplay_actions": sum(row["request"]["path"] in {"/api/action", "/api/chat"} for row in ROWS),
        "mean_ms": round(sum(row["http_ms"] for row in ROWS) / len(ROWS), 1),
        "max_ms": round(max(row["http_ms"] for row in ROWS), 1),
        "hidden_exposures": sum(bool(row["hidden_exposures"]) for row in ROWS),
        "provider": "offline fixture; no live provider dispatch",
        "elapsed_s": round(time.perf_counter() - started, 1),
        "cross_campaign_transcripts_distinct": True,
    }
    (OUT / "http_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
