"""PR-PLAY-79 holdout, HTTP campaigns, and protected-file check.

The holdout file is written by `freeze` and then only read.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
FIXTURE = OUT / "holdout_cases.json"


def _intent_cases():
    rows = []
    samples = [
        ("I want to follow the tracks farther.", "success_without_discovery"),
        ("I try to determine which direction the patrol went.", "success_without_discovery"),
        ("I search for a route along the road.", "success_without_discovery"),
        ("I chase the prints.", "success_without_discovery"),
        ("I trace the trail.", "success_without_discovery"),
        ("I peer down the road.", "success_without_discovery"),
        ("I scan the road ahead.", "success_without_discovery"),
        ("I look farther along the track.", "success_without_discovery"),
        ("I gaze down the road.", "success_without_discovery"),
        ("I view the road ahead.", "success_without_discovery"),
        ("Which direction did the prints go?", "success_without_discovery"),
        ("I follow the prints.", "success_without_discovery"),
        ("I pursue the trail.", "success_without_discovery"),
        ("I wait to see whether anyone comes along.", "read_only"),
        ("I wait quietly.", "read_only"),
        ("I watch the road for a while.", "read_only"),
        ("What is visible from here?", "read_only"),
        ("Rather than report, I keep examining.", "read_only"),
        ("Before I report, I look around the stone.", "read_only"),
        ("I leave a marker so I can find this place again.", "missing_mechanic"),
        ("I place a cairn beside the road.", "missing_mechanic"),
        ("I set a cairn by the road.", "missing_mechanic"),
        ("Look over there.", "clarify"),
        ("Move that.", "clarify"),
        ("Ask them.", "clarify"),
        ("Move it.", "clarify"),
        ("I climb the marker.", "missing_mechanic"),
        ("I look for a secret passage under the stone.", "needs_authority"),
        ("I look for buried treasure.", "needs_authority"),
        ("Describe the texture of the stone.", "not_promoted"),
        ("I scan farther down the road.", "success_without_discovery"),
        ("I look ahead along the prints.", "success_without_discovery"),
        ("What do we know?", "read_only"),
        ("I watch the road.", "read_only"),
        ("Ask over there.", "clarify"),
        ("I scale the marker.", "missing_mechanic"),
        ("I balance on the marker.", "missing_mechanic"),
        ("I create a secret passage.", "needs_authority"),
        ("I summon a guide.", "needs_authority"),
        ("Is there a stable grip here?", "not_promoted"),
        ("I leave a blaze on the post.", "missing_mechanic"),
        ("Shift it.", "clarify"),
        ("I search under the loose stone.", "success_without_discovery"),
        ("I dig beside the marker.", "success_without_discovery"),
        ("I look for a handhold.", "cannot_attempt"),
    ]
    for text, outcome in samples:
        rows.append({"lane": "intent", "text": text, "outcome": outcome, "multi_turn": False, "save": False, "cross": False})
    return rows


def _narration_cases():
    rows = [
        ("You arrive at the Rain Barrel Tavern and the room is warm.", "old_milestone", False, "other_location"),
        ("Rain spatters soot-dark stone across Cinderwatch's eastern gate while banners snap.", "old_milestone", False, "other_location"),
        ("You stand in the Rain Barrel Tavern while the fire pops.", "old_milestone", False, "other_location"),
        ("You enter the Investigator's Office and shut the door behind you.", "old_milestone", False, "other_location"),
        ("You find yourself in the Cinderwatch Market Quarter among the stalls tonight.", "old_milestone", False, "other_location"),
        ("You are still at Old Milestone. The prints fade into the scrub ahead of you.", "old_milestone", False, None),
        ("You are at Old Milestone. The prints still fade into the scrub.", "old_milestone", False, None),
        ("You arrive at Cinderwatch's gate while the banners snap overhead.", "frontier_gate", False, None),
        ("The mud around the marker is churned with faint overlapping prints that fade.", "old_milestone", False, None),
        ("You arrive at the Rain Barrel Tavern and the room is warm.", "frontier_gate", True, None),
        ("You shove the loose stone aside and leave the ground bare where it had been sitting.", "old_milestone", False, "object_state"),
        ("The loose stone is beside the stonework, and it has not been moved from that place.", "old_milestone", False, None),
        ("The hidden patrol captain waits behind the ridge with the payroll, and he waves you over now.", "old_milestone", False, "hidden_fact"),
        ("You are still at Old Milestone. No travel was completed, so another place was not published.", "old_milestone", False, None),
        ("Dust lifts around the old milestone while you stay with the prints.", "old_milestone", False, None),
    ]
    return [{"lane": "narration", "text": text, "scene_id": scene, "transition": moved, "reason": reason,
             "multi_turn": False, "save": False, "cross": True} for text, scene, moved, reason in rows]


def _dialogue_cases():
    lines = [
        ("Hello, Mara.", "hello"),
        ("Who are you?", "mara"),
        ("What is this place like?", "traveler is here"),
        ("What do you make of the marker?", "marker"),
        ("Have you seen the patrol?", "do not know"),
        ("I tell you the prints are unclear.", "whether"),
        ("What did I tell you?", "prints"),
        ("Thank you, Mara.", "thank"),
        ("Have you seen any soldiers?", "do not know"),
        ("Tell me about the secret camp.", "do not know"),
        ("Ask Mara to promise a reward.", "do not know"),
        ("Does she seem worried?", "reserved"),
        ("Goodbye, Mara.", "mara"),
        ("Ask Mara about the area.", "mara"),
        ("Thanks, Mara.", "thank"),
    ]
    return [{"lane": "dialogue", "text": text, "fragment": fragment, "multi_turn": True, "save": False, "cross": True} for text, fragment in lines]


def _action_cases():
    rows = [
        ("Move the stone aside and inspect the ground beneath it.", "aside"),
        ("Move the stone aside and look around the yard.", "aside"),
        ("Move the stone aside, climb the marker, and ask the traveler what they saw.", "aside"),
        ("Look around the yard and wait and watch the road.", "look around"),
        ("Greet the traveler and ask who they are.", "mara"),
        ("Ask the traveler about the road, thank them, and move away.", "thank"),
        ("I look for signs of a struggle.", "no signs"),
        ("I offer to help search.", "no search party"),
        ("I wait and watch the road.", "nothing new"),
        ("I inspect the tracks more closely.", "not established"),
        ("Move the stone aside.", "aside"),
        ("Where is the loose stone?", "stonework"),
        ("I stand up.", "stand"),
        ("Approach the traveler and step back.", "move away"),
        ("Fly over the wall and look around the yard.", "not supported"),
    ]
    return [{"lane": "action", "text": text, "fragment": fragment, "multi_turn": True, "save": False, "cross": True} for text, fragment in rows]


def freeze():
    cases = _intent_cases() + _narration_cases() + _dialogue_cases() + _action_cases()
    # Fifteen actual save/resume steps are executed by the runner, not by rewriting this file.
    for index in range(15):
        cases.append({
            "lane": "save",
            "text": f"What is visible from here? #{index + 1}",
            "multi_turn": True,
            "save": True,
            "cross": False,
        })
    payload = {
        "cycle": "PR-PLAY-79",
        "authored_by": "developer",
        "external_validation": False,
        "cases": cases,
    }
    raw = json.dumps(payload, indent=2).encode("utf-8")
    FIXTURE.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    (OUT / "holdout_hash.txt").write_text(digest + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(cases), "hash": digest}))


def _boot(name):
    from tests.helpers.storage_isolation import install
    install(OUT / name)
    os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
    os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_BRANCHING"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_DYNAMIC_NPCS"] = "1"
    os.environ["ASHEN_BOUNDED_SPEECH"] = "1"


def holdout():
    _boot("holdout_data")
    frozen = json.loads(FIXTURE.read_text(encoding="utf-8"))
    digest = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    recorded = (OUT / "holdout_hash.txt").read_text(encoding="utf-8").strip()
    from game.general_purpose_actions import classify
    from game.narrative_consistency import publication_conflict
    from game.bounded_improvisation import LEDGER_KEY
    from tests.test_pr_play_78_integrated import play, prepare, stage
    from tests.test_pr_play_79_agency import milestone
    session, scene, world = milestone()
    traveler_session, traveler_scene, traveler_world = stage()
    prepare("mixed", traveler_session, traveler_scene)
    results = []
    for index, case in enumerate(frozen["cases"], start=1):
        ok = True
        detail = ""
        lane = case["lane"]
        if lane == "intent":
            proposal = classify(case["text"], scene=scene, world=world, session=session)
            ok = bool(proposal) and proposal.get("outcome") == case["outcome"]
            detail = None if not proposal else proposal.get("outcome")
        elif lane == "narration":
            local = dict(session)
            local["active_scene_id"] = case["scene_id"]
            if case["text"].startswith("You shove the loose stone"):
                from tests.test_pr_play_76_physical import add
                add(local, ident="stone", label="loose stone", aliases=["stone"], scene_id="old_milestone", position="beside the stonework")
            conflict = publication_conflict(case["text"], session=local, resolution={"resolved_transition": case["transition"]}, scene=scene)
            if case["reason"]:
                ok = bool(conflict) and case["reason"] in conflict
            else:
                ok = conflict is None
            detail = conflict
        elif lane == "dialogue":
            _plan, _result, said, _changed = play(case["text"], traveler_session, traveler_scene, traveler_world)
            ok = case["fragment"] in said.casefold() and "northwest" not in said.casefold()
            detail = said[:180]
        elif lane == "action":
            _plan, _result, said, _changed = play(case["text"], traveler_session, traveler_scene, traveler_world)
            ok = case["fragment"] in said.casefold()
            detail = said[:180]
        elif lane == "save":
            continue
        results.append({"id": f"H{index:03d}", "lane": lane, "ok": ok, "detail": detail, "text": case["text"]})
    save_rows = _save_block()
    results.extend(save_rows)
    passed = sum(1 for row in results if row["ok"])
    summary = {
        "hash": digest,
        "hash_matches_freeze": digest == recorded,
        "passed": passed,
        "failed": len(results) - passed,
        "total": len(results),
        "multi_turn": sum(1 for case in frozen["cases"] if case.get("multi_turn")),
        "save_cases": sum(1 for row in results if row["lane"] == "save"),
        "cross": sum(1 for case in frozen["cases"] if case.get("cross")),
        "narration": sum(1 for case in frozen["cases"] if case["lane"] == "narration"),
        "external_validation": False,
    }
    (OUT / "holdout_results.json").write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def _save_block():
    import copy
    from fastapi.testclient import TestClient
    from game import api, storage
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
    api.call_gpt = lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
    api.log_upstream_api_preflight_at_startup = lambda: None
    from tests.test_pr_play_71_lifecycle import create, flags, reach, safe, start
    rows = []
    with TestClient(api.app) as client:
        identity = create(client)
        start(client)
        reach(client)
        for index in range(15):
            text = "What is visible from here?"
            before_scene = storage.load_session().get("active_scene_id")
            before_flags = copy.deepcopy(flags())
            spoken = safe(client.post("/api/chat", json={"text": text}))
            snap = safe(client.post("/api/snapshots", json={"label": f"holdout-save-{index}"}))["snapshot"]["id"]
            create(client)
            safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
            restored = storage.load_session()
            ok = (
                restored.get("campaign_run_id") == identity
                and restored.get("active_scene_id") == before_scene
                and flags().get("patrol_survey") is not True
                and flags().get("patrol_report") is not True
                and bool(spoken["gm_output"]["player_facing_text"])
            )
            rows.append({
                "id": f"S{index + 1:02d}",
                "lane": "save",
                "ok": ok,
                "text": text,
                "detail": restored.get("active_scene_id"),
                "flags": before_flags,
            })
    return rows


def http():
    import copy
    _boot("http_data")
    from fastapi.testclient import TestClient
    from game import api, storage
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
    api.call_gpt = lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
    api.log_upstream_api_preflight_at_startup = lambda: None
    from tests.test_pr_play_71_lifecycle import create, flags, safe, start
    campaigns = {
        "authored": [
            "I examine the notice board.",
            "I follow the missing patrol rumor.",
            "I examine the weathered milestone.",
            "I return to report the uncertain trail to the watch.",
            "I return to Cinderwatch Gate.",
            "I give the watch my patrol report.",
        ],
        "initiative": [
            "I examine the notice board.",
            "I follow the missing patrol rumor.",
            "I examine the weathered milestone.",
            "I want to follow the tracks farther.",
            "I wait to see whether anyone comes along.",
            "I leave a marker so I can find this place again.",
            "I look around.",
            "What do we know about the prints?",
        ],
    }
    report = {}
    with TestClient(api.app) as client:
        for name, lines in campaigns.items():
            create(client)
            start(client)
            turns = []
            samples = []
            for text in lines:
                before = {"scene": storage.load_session().get("active_scene_id"), "flags": copy.deepcopy(flags())}
                clock = time.perf_counter()
                payload = safe(client.post("/api/chat", json={"text": text}))
                elapsed = round((time.perf_counter() - clock) * 1000, 1)
                samples.append(elapsed)
                turns.append({
                    "input": text,
                    "elapsed_ms": elapsed,
                    "before": before,
                    "after": {"scene": storage.load_session().get("active_scene_id"), "flags": copy.deepcopy(flags())},
                    "player_facing_text": payload["gm_output"]["player_facing_text"],
                })
            snap = safe(client.post("/api/snapshots", json={"label": name}))["snapshot"]["id"]
            saved_scene = storage.load_session().get("active_scene_id")
            saved_flags = copy.deepcopy(flags())
            create(client)
            safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
            resumed = {
                "scene": storage.load_session().get("active_scene_id"),
                "flags": copy.deepcopy(flags()),
                "matched": storage.load_session().get("active_scene_id") == saved_scene and flags() == saved_flags,
            }
            report[name] = {"turns": turns, "resume": resumed, "latency_ms": samples}
    (OUT / "http_campaigns.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({name: {"turns": len(body["turns"]), "resume": body["resume"]["matched"], "last": body["turns"][-1]["player_facing_text"][:180]} for name, body in report.items()}, indent=2))


def hashes():
    prior = json.loads((ROOT / "artifacts" / "pr_play_78a" / "protected_hashes.json").read_text(encoding="utf-8"))
    baseline = json.loads((ROOT / "artifacts" / "pr_play_78" / "protected_before.json").read_text(encoding="utf-8"))
    mismatches = []
    missing = []
    for row in baseline["files"]:
        path = ROOT / row["path"]
        if not path.exists():
            missing.append(row["path"])
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row["sha256"]:
            mismatches.append(row["path"])
    result = {
        "expected": baseline["count"],
        "preserved": baseline["count"] - len(mismatches) - len(missing),
        "mismatches": mismatches,
        "missing": missing,
        "prior_cycle_preserved": prior.get("preserved"),
    }
    (OUT / "protected_hashes.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


def live():
    """One extended session with the live provider left on. The player is a visible-text policy."""
    import copy
    from fastapi.testclient import TestClient
    from tests.helpers.storage_isolation import install
    install(OUT / "live_data")
    os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
    os.environ.pop("ASHEN_DISABLE_PROVIDER_CALLS", None)
    os.environ.pop("ASHEN_DISABLE_EXPRESSION_GENERATION", None)
    os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)
    os.environ["ASHEN_EXPERIMENTAL_BRANCHING"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_DYNAMIC_NPCS"] = "1"
    os.environ["ASHEN_BOUNDED_SPEECH"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION"] = "1"
    from game import api, storage
    api.log_upstream_api_preflight_at_startup = lambda: None
    from tests.test_pr_play_71_lifecycle import create, flags, safe, start
    from game.integrated_play import presentation_usage
    policy = [
        "Hello, captain.",
        "Who are you?",
        "What is this place like?",
        "Have you seen the patrol?",
        "I tell you I have not left the gate yet.",
        "What did I tell you?",
        "I look around the gate and ask the captain what he sees.",
        "I cast a spell to reveal the patrol.",
        "I examine the notice board.",
        "I follow the missing patrol rumor.",
        "I examine the weathered milestone.",
        "I want to follow the tracks farther.",
        "I wait to see whether anyone comes along.",
        "I leave a marker so I can find this place again.",
        "I look for signs of a struggle.",
        "I search for a route along the road.",
        "What do we know about the prints?",
        "I look around.",
        "Before I report, I want to keep looking.",
        "I ask the guard to send someone with me.",
        "I return to Cinderwatch Gate.",
        "Ask the captain whether the tracks matter.",
        "I tell the captain the prints are unclear.",
        "What did I tell you?",
        "Thank you, captain.",
        "I look around.",
        "What is visible from here?",
        "I wait quietly.",
        "I peer down the road.",
        "Rather than report, I keep examining.",
        "I survey the uncertain trail myself.",
        "I record the limits of the survey.",
    ]
    # The list is a visible-text policy with a bounded repertoire, not an unguided person.
    transcript = []
    samples = []
    with TestClient(api.app) as client:
        create(client)
        started = time.perf_counter()
        start(client)
        samples.append(round((time.perf_counter() - started) * 1000, 1))
        seen = []
        for text in policy:
            if seen.count(text) >= 2:
                continue
            seen.append(text)
            before = {"scene": storage.load_session().get("active_scene_id"), "flags": copy.deepcopy(flags())}
            clock = time.perf_counter()
            payload = safe(client.post("/api/chat", json={"text": text}))
            elapsed = round((time.perf_counter() - clock) * 1000, 1)
            samples.append(elapsed)
            said = payload["gm_output"]["player_facing_text"]
            current = storage.load_session()
            audit = current.get("last_background_expression") if isinstance(current, dict) else None
            narration = current.get("last_narration") if isinstance(current, dict) else None
            transcript.append({
                "input": text,
                "provenance": "bounded repertoire chosen for visible beats; not a human and not an unscripted agent",
                "elapsed_ms": elapsed,
                "before": before,
                "after": {"scene": current.get("active_scene_id"), "flags": copy.deepcopy(flags())},
                "player_facing_text": said,
                "dialogue_adopted": bool(isinstance(audit, dict) and audit.get("adopted")),
                "narration_adopted": bool(isinstance(narration, dict) and narration.get("adopted")),
            })
            usage_path = Path(os.environ["ASHEN_DATA_DIR"]) / "provider_usage.jsonl"
            spent = 0
            if usage_path.exists():
                spent = sum(1 for line in usage_path.read_text(encoding="utf-8").splitlines() if line.strip())
            if spent >= 36:
                break
        snap = safe(client.post("/api/snapshots", json={"label": "live"}))["snapshot"]["id"]
        saved = {"scene": storage.load_session().get("active_scene_id"), "flags": copy.deepcopy(flags())}
        create(client)
        safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
        resumed = storage.load_session().get("active_scene_id") == saved["scene"] and flags() == saved["flags"]
        again = safe(client.post("/api/chat", json={"text": "What do we know about the prints?"}))
        transcript.append({
            "input": "What do we know about the prints?",
            "provenance": "resume continuation",
            "player_facing_text": again["gm_output"]["player_facing_text"],
            "after": {"scene": storage.load_session().get("active_scene_id"), "flags": copy.deepcopy(flags())},
        })
    ordered = sorted(samples)
    def pct(p):
        return ordered[min(len(ordered) - 1, max(0, int(round((p / 100) * (len(ordered) - 1)))))]
    usage_path = Path(os.environ["ASHEN_DATA_DIR"]) / "provider_usage.jsonl"
    provider_rows = []
    if usage_path.exists():
        provider_rows = [json.loads(line) for line in usage_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    tokens = sum(int((row.get("total_tokens") or 0)) for row in provider_rows)
    record = {
        "turns": len(transcript),
        "resume": resumed,
        "latency_ms": {"mean": round(sum(samples) / len(samples), 1), "p95": pct(95), "max": max(samples), "n": len(samples)},
        "presentation": presentation_usage(),
        "provider_requests": len(provider_rows),
        "provider_tokens": tokens,
        "transcript": transcript,
    }
    (OUT / "live_session.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({key: record[key] for key in ("turns", "resume", "latency_ms", "provider_requests", "provider_tokens", "presentation")}, indent=2)[:4000])


def speak():
    """Continue the saved live session and address the Gate Guard by name."""
    import copy
    from fastapi.testclient import TestClient
    from tests.helpers.storage_isolation import install
    install(OUT / "live_data")
    os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
    os.environ.pop("ASHEN_DISABLE_PROVIDER_CALLS", None)
    os.environ.pop("ASHEN_DISABLE_EXPRESSION_GENERATION", None)
    os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)
    for key in (
        "ASHEN_EXPERIMENTAL_BRANCHING", "ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS",
        "ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE", "ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION",
        "ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", "ASHEN_EXPERIMENTAL_DYNAMIC_NPCS",
        "ASHEN_BOUNDED_SPEECH", "ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION",
    ):
        os.environ[key] = "1"
    from game import api, storage
    api.log_upstream_api_preflight_at_startup = lambda: None
    from tests.test_pr_play_71_lifecycle import flags, safe
    lines = [
        "Talk to the Gate Guard.",
        "Who are you?",
        "What is this place like?",
        "Have you seen the patrol?",
        "I tell you the prints at the milestone are unclear.",
        "What did I tell you?",
        "Do you think the tracks matter?",
        "Thank you.",
    ]
    usage_path = Path(os.environ["ASHEN_DATA_DIR"]) / "provider_usage.jsonl"
    def completed():
        if not usage_path.exists():
            return 0
        return sum(1 for line in usage_path.read_text(encoding="utf-8").splitlines() if '"event": "completed"' in line)
    before = completed()
    rows = []
    with TestClient(api.app) as client:
        for text in lines:
            if completed() - before >= 10:
                break
            clock = time.perf_counter()
            payload = safe(client.post("/api/chat", json={"text": text}))
            meta = (payload.get("gm_output") or {}).get("metadata") or {}
            expr = meta.get("expression_generation") or {}
            rows.append({
                "input": text,
                "elapsed_ms": round((time.perf_counter() - clock) * 1000, 1),
                "scene": storage.load_session().get("active_scene_id"),
                "flags": copy.deepcopy(flags()),
                "player_facing_text": payload["gm_output"]["player_facing_text"],
                "expression_decision": expr.get("decision"),
                "expression_adopted": expr.get("decision") == "adopted",
            })
    record = {"turns": rows, "completed_requests_added": completed() - before}
    (OUT / "live_dialogue_talk.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2)[:5000])


if __name__ == "__main__":
    {"freeze": freeze, "holdout": holdout, "http": http, "hashes": hashes, "live": live, "speak": speak}[sys.argv[1]]()
