"""Execute the preimplementation developer holdout once; never tune this manifest."""
import os
os.environ["PR72_STORAGE"] = "holdout_data"
os.environ["PR72_NETWORK"] = "holdout_network.jsonl"
import hashlib
import json
from pathlib import Path
import time
from runtime import api, storage, OUT, snapshot
from artifacts.pr_play_67.http_harness import server
from tests.test_pr_play_71_lifecycle import byid


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def main():
    lock = OUT / "holdout_started.json"
    with lock.open("x") as f: json.dump({"started": time.time(), "policy": "one execution; preserve failures"}, f)
    rows = json.loads((OUT / "frozen_holdout.json").read_text())
    manifest = json.loads((OUT / "frozen_holdout_manifest.json").read_text())
    assert hashlib.sha256((OUT / "frozen_holdout.json").read_bytes()).hexdigest() == manifest["sha256"]
    # Hidden canaries enter disposable authored templates, never runtime seeding.
    for path in storage.SCENES_DIR.glob("*.json"):
        data = json.loads(path.read_text()); data["scene"]["gm_notes"] = "SENTINEL_PR72_PRIVATE"
        path.write_text(json.dumps(data))
    results = []; slots = {}
    with server() as request:
        def call(path, payload=None):
            response = request(path, payload)
            assert response["status"] == 200, response
            return response["body"]
        def chat(text): return call("/api/chat", {"text": text})
        def act(aid):
            a = byid(aid)
            return call("/api/action", {"action_type": "exploration", "intent": a["label"], "exploration_action": {"id": aid, "type": "custom", "label": a["label"]}})
        for branch in ("survey", "report"):
            call("/api/new_campaign", {}); call("/api/start_campaign", {})
            chat("I examine the notice board."); chat("I follow the missing patrol rumor."); chat("I examine the weathered milestone.")
            act("patrol_" + branch)
            if branch == "report": chat("I return to Cinderwatch Gate.")
            act("patrol_record_survey" if branch == "survey" else "patrol_warn_watch")
            slots[branch] = call("/api/snapshots", {"label": "holdout-" + branch})["snapshot"]["id"]
        for case in rows:
            call("/api/snapshots/load", {"snapshot_id": slots[case["start"]["branch"]]})
            before = snapshot(); response = request("/api/chat", {"text": case["text"]}); after = snapshot()
            capture = json.loads((OUT / "holdout_network.jsonl").read_text().splitlines()[-1])
            d = capture["stages"].get("interpretation") or {}
            log = storage.load_log()[-1]
            expected = case["expected"]
            text = response["body"].get("gm_output", {}).get("player_facing_text", "") if isinstance(response["body"], dict) else ""
            checks = {"http_ok": response["status"] == 200, "category": d.get("category") == expected["category"],
                      "operation": d.get("proposed_operation") == expected["operation"], "target": d.get("proposed_target") == expected["target"],
                      "nonexecuting_state_unchanged": expected["category"] == "EXECUTE" or before == after,
                      "no_hidden_exposure": "SENTINEL_PR72_PRIVATE" not in response["serialized_body"],
                      "no_internal_metadata": all(t not in response["serialized_body"] for t in ['"proposed_record"', '"gm_notes"', '"world_state"', '"hidden_facts"']),
                      "nonempty_publication": bool(text)}
            other = "watch has now been warned" if case["start"]["branch"] == "survey" else "survey is now recorded"
            checks["no_unchosen_followup"] = other not in text
            if expected["category"] == "EXECUTE":
                resolution = log.get("resolution", {})
                checks["resolved_action"] = resolution.get("success") is True and resolution.get("action_id") == expected["target"]
            persistence = None
            if case["group"] == "resume":
                saved = call("/api/snapshots", {"label": case["id"]})["snapshot"]["id"]
                transcript = call("/api/log")
                call("/api/snapshots/load", {"snapshot_id": saved})
                restored = snapshot(); left = json.loads(json.dumps(after)); right = json.loads(json.dumps(restored))
                for value in (left, right):
                    value["session"].pop("last_saved_at", None)
                    # Resume marker is intentionally managed by the existing endpoint.
                    value["session"].pop("narration_resume_entry_pending", None)
                persistence = dict(snapshot_id=saved, transcript_restored=call("/api/log") == transcript, flags_restored=after["world"] == restored["world"], identity_restored=after["session"]["campaign_run_id"] == restored["session"]["campaign_run_id"])
                checks["persistence"] = all(persistence[k] for k in ("transcript_restored", "flags_restored", "identity_restored"))
            results.append(dict(id=case["id"], group=case["group"], text=case["text"], expected=expected,
                                interpretation=d, action_resolution=log.get("resolution"), checks=checks, passed=all(checks.values()),
                                authority_before_sha256=digest(before), authority_after_sha256=digest(after), response=response["body"],
                                http_ms=response["http_ms"], stages=capture["stages"], persistence=persistence))
            (OUT / "holdout_results.json").write_text(json.dumps(results, indent=2))
    summary = dict(cases=len(results), passed=sum(r["passed"] for r in results), failed=[dict(id=r["id"], checks=[k for k,v in r["checks"].items() if not v]) for r in results if not r["passed"]], manifest_sha256=manifest["sha256"], executions=1, authorship=manifest["authorship"])
    (OUT / "holdout_summary.json").write_text(json.dumps(summary, indent=2)); print(summary)


if __name__ == "__main__": main()
