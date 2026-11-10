"""One execution of the frozen PR-PLAY-73 holdout. Does not edit the frozen file."""
import os
os.environ["PR73_STORAGE"] = "holdout_data"
os.environ["PR73_NETWORK"] = "holdout_network.jsonl"
import hashlib
import json
from runtime import OUT, snapshot, storage
from artifacts.pr_play_67.http_harness import server
from game.general_purpose_actions import classify
from game.player_initiative import decide


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clues(state):
    return list((state["session"] or {}).get("discovered_clues") or [])


def flags(state):
    return dict(((state["world"] or {}).get("world_state") or {}).get("flags") or {})


def main():
    manifest = json.loads((OUT / "frozen_holdout_manifest.json").read_text(encoding="utf-8"))
    assert digest(OUT / "frozen_holdout.json") == manifest["sha256"]
    assert digest(OUT / "frozen_start_states.json") == manifest["states_sha256"]
    marker = OUT / "holdout_started.json"
    if marker.exists():
        raise SystemExit("Holdout already started. Refusing a second execution.")
    marker.write_text(json.dumps({"executions": 1, "manifest_sha256": manifest["sha256"]}), encoding="utf-8")
    cases = json.loads((OUT / "frozen_holdout.json").read_text(encoding="utf-8"))
    slots = json.loads((OUT / "holdout_slots.json").read_text(encoding="utf-8"))
    results = []
    with server() as request:
        for case in cases:
            loaded = request("/api/snapshots/load", {"snapshot_id": slots[case["branch"]]})
            assert loaded["status"] == 200, loaded
            before = snapshot()
            from game import api
            scene = api.load_active_scene()
            proposal = classify(case["text"], scene=scene, world=before["world"], session=before["session"])
            decision = decide(case["text"], scene=scene, world=before["world"], session=before["session"])
            row = request("/api/chat", {"text": case["text"]})
            after = snapshot()
            published = ""
            if isinstance(row["body"], dict):
                published = ((row["body"].get("gm_output") or {}).get("player_facing_text") or "")
            expected = case["expected"]
            checks = {
                "http": row["status"] == 200,
                "hidden": not row["hidden_exposures"],
                "projection": all(token not in row["serialized_body"] for token in ('"gm_notes"', '"hidden_facts"', '"proposed_record"', "SENTINEL_")),
                "decision": decision is not None and decision.category.value == expected["decision"],
                "reason": decision is not None and expected["reason"] in decision.reason,
                "flags": flags(before) == flags(after),
                "clues": clues(before) == clues(after),
                "scene": before["session"]["active_scene_id"] == after["session"]["active_scene_id"],
            }
            if expected["gp_category"] is None:
                checks["not_gp"] = proposal is None or not str(decision.reason).startswith("initiative_gp_")
            else:
                checks["gp_category"] = proposal is not None and proposal.get("category") == expected["gp_category"]
                checks["gp_family"] = proposal is not None and proposal.get("family") == expected["gp_family"]
                checks["gp_readonly"] = proposal is not None and proposal.get("mutation") is False
            if expected["state_unchanged"]:
                checks["state"] = before == after
            for phrase in expected["publication_any"]:
                checks["pub:" + phrase] = phrase in published
            for phrase in expected["publication_none"]:
                checks["forbid:" + phrase] = phrase not in published
            if expected["persist"]:
                saved = request("/api/snapshots", {"label": case["id"]})
                transcript = request("/api/log")
                request("/api/snapshots/load", {"snapshot_id": saved["body"]["snapshot"]["id"]})
                restored = snapshot()
                checks["resume_flags"] = flags(restored) == flags(after)
                checks["resume_clues"] = clues(restored) == clues(after)
                checks["resume_scene"] = restored["session"]["active_scene_id"] == after["session"]["active_scene_id"]
                checks["resume_log"] = request("/api/log")["body"] == transcript["body"]
            results.append({
                "id": case["id"], "text": case["text"], "passed": all(checks.values()),
                "checks": checks, "published": published,
                "proposal": proposal, "reason": None if decision is None else decision.reason,
                "http_ms": row["http_ms"],
            })
            (OUT / "holdout_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    failed = [row for row in results if not row["passed"]]
    summary = {
        "cases": len(results),
        "passed": len(results) - len(failed),
        "failed": [{"id": row["id"], "text": row["text"], "checks": [key for key, value in row["checks"].items() if not value], "reason": row["reason"], "published": row["published"], "proposal_category": None if not row["proposal"] else row["proposal"].get("category")} for row in failed],
        "executions": 1,
        "manifest_sha256": manifest["sha256"],
        "authorship": manifest["authorship"],
    }
    (OUT / "holdout_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
