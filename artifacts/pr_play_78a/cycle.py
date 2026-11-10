"""PR-PLAY-78A verification. Isolation is installed before any game import.

Commands: freeze, holdout, http, adaptive, provider, hashes, devcount
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
MANIFEST = OUT / "holdout_manifest.json"
HASH_FILE = OUT / "holdout_hash.txt"

PARAPHRASES = [
    ("I return to report the uncertain trail to the watch.", "execute", "patrol_report"),
    ("I head back and tell the watch what I found.", "execute", "patrol_report"),
    ("I'll report these tracks to the guards.", "execute", "patrol_report"),
    ("I go back to Cinderwatch and give my report.", "execute", "patrol_report"),
    ("I tell the watch that the trail is uncertain.", "execute", "patrol_report"),
    ("Please report the uncertain trail to the watch.", "execute", "patrol_report"),
    ("Report the uncertain trail to the watch.", "execute", "patrol_report"),
    ("I would like to report the uncertain trail.", "execute", "patrol_report"),
    ("I am going to report the uncertain prints.", "execute", "patrol_report"),
    ("The tracks should be reported to the watch.", "execute", "patrol_report"),
    ("I bring the uncertain trail to the watch.", "execute", "patrol_report"),
    ("Kindly report the uncertain trail.", "execute", "patrol_report"),
    ("We report the trail to the watch.", "execute", "patrol_report"),
    ("I survey the uncertain trail myself.", "execute", "patrol_survey"),
    ("I record the survey at the milestone.", "execute", "patrol_survey"),
    ("I document what I found at the milestone.", "execute", "patrol_survey"),
    ("Let's record our findings on the trail.", "execute", "patrol_survey"),
    ("I make a note of the uncertain trail.", "execute", "patrol_survey"),
    ("I write down the tracks we discovered at the milestone.", "execute", "patrol_survey"),
    ("I will survey the uncertain prints.", "execute", "patrol_survey"),
    ("I survey the overlapping prints.", "execute", "patrol_survey"),
    ("Write down the survey of the trail.", "execute", "patrol_survey"),
    ("Let me survey the trail.", "execute", "patrol_survey"),
    ("I note the uncertain tracks at the milestone.", "execute", "patrol_survey"),
    ("I will document the uncertain trail.", "execute", "patrol_survey"),
]
UNAVAILABLE = [
    ("I perform the secret rite.", "hidden", "none", None),
    ("I survey the uncertain trail myself.", "no_clues", "decline", None),
    ("I survey the uncertain trail myself.", "survey_done", "decline", None),
    ("I record the limits of your survey.", "ready", "not_record", None),
    ("Give the watch your patrol report.", "ready", "decline", "wrong_scene"),
    ("I return to report the uncertain trail to the watch.", "other", "none", None),
    ("I give the watch my patrol report.", "gate", "decline", None),
    ("I walk toward the town gate.", "ready", "none", None),
    ("Survey the distant galaxy.", "ready", "none", None),
    ("I want to report a programming bug.", "ready", "none", None),
    ("Please report my inventory.", "ready", "none", None),
    ("I give the watch your patrol report.", "ready", "decline", None),
    ("What can I do here?", "hidden", "answer", None),
    ("I return to report the uncertain trail to the watch.", "report_done", "decline", None),
    ("I give the watch my patrol report.", "gate_report", "execute", "patrol_warn_watch"),
]
SPEECH = [
    ("Should I report the uncertain trail?", "decline"),
    ("What happens if I report the uncertain trail?", "decline"),
    ("I don't want to report the uncertain trail.", "decline"),
    ("If I reported the trail, would the watch believe me?", "answer"),
    ("Can I report the trail yet?", "answer"),
    ('"I return to report the uncertain trail to the watch."', "decline"),
    ("The notice says report the uncertain trail.", "decline"),
    ("Suppose I report the uncertain trail.", "decline"),
    ("I was thinking about reporting the uncertain trail.", "decline"),
    ("I will not report the trail to the watch.", "decline"),
    ("I do not survey the uncertain trail.", "decline"),
    ("What if I survey the uncertain trail?", "decline"),
    ("I never report the uncertain trail.", "decline"),
    ("Could you survey the uncertain trail.", "answer"),
    ("If the trail beyond the stone is clear, follow it; otherwise I stay and tell the watch what I saw.", "decline"),
]
PROGRESS = [
    "What can I do here?",
    "What are my options?",
    "What should I investigate next?",
    "Can I survey the uncertain trail yet?",
    "Am I able to report the trail yet?",
    "What can I do here?",
    "What are my options?",
    "What should I do next?",
    "What should I investigate next?",
    "What can I do here?",
]
OPENING = "Rain spatters soot-dark stone across Cinderwatch's eastern gate while frayed banners snap."


def _case(index, **fields):
    fields["id"] = f"H{index:03d}"
    return fields


def build_cases():
    cases = []
    n = 1
    for text, kind, ident in PARAPHRASES:
        cases.append(_case(n, lane="paraphrase", type="propose", setup="ready", text=text, expect={"kind": kind, "id": ident}, nontrivial=True))
        n += 1
    for text, setup, kind, reason in UNAVAILABLE:
        expect = {"kind": kind}
        if reason:
            expect["reason"] = reason
        if kind == "execute":
            expect["id"] = reason
            expect.pop("reason", None)
        if text.startswith("What can"):
            expect["forbids"] = ["secret rite"]
        cases.append(_case(n, lane="unavailable", type="propose", setup=setup, text=text, expect=expect))
        n += 1
    for text, kind in SPEECH:
        cases.append(_case(n, lane="speech", type="propose", setup="ready", text=text, expect={"kind": kind}))
        n += 1
    for text in PROGRESS:
        cases.append(_case(n, lane="progress", type="propose", setup="hidden", text=text, expect={"kind": "answer", "forbids": ["secret rite", "patrol_"]}))
        n += 1
    cases.append(_case(n, lane="ambiguity", type="propose", setup="ready", text="I want to follow up on the patrol.", expect={"kind": "clarify"})); n += 1
    cases.append(_case(n, lane="movement", type="propose", setup="ready", text="I head toward the crates.", expect={"kind": "none"})); n += 1
    cases.append(_case(n, lane="movement", type="propose", setup="ready", text="I pick up a pebble.", expect={"kind": "none"})); n += 1
    cases.append(_case(n, lane="movement", type="propose", setup="ready", text="Hello there.", expect={"kind": "none"})); n += 1
    cases.append(_case(n, lane="movement", type="propose", setup="ready", text="I look at the mud.", expect={"kind": "none"})); n += 1
    for label, active, transition, replaced in (
        ("foreign opening stays off the milestone", "old_milestone", False, True),
        ("foreign opening is legal at the gate", "frontier_gate", False, False),
        ("a committed transition may keep destination text", "old_milestone", True, False),
    ):
        cases.append(_case(
            n, lane="scene", type="scene", text=OPENING, active=active,
            resolved_transition=transition, expect={"replaced": replaced}, note=label,
        ))
        n += 1
    http = [
        ("mixed", "Examine the notice board and ask the guard about the warning.", {"contains": "northwest mud", "scene": "frontier_gate", "flag_absent": "patrol_survey"}),
        ("mixed", "I read the notice board, then ask the guard what the warning means.", {"scene": "frontier_gate", "flag_absent": "patrol_report"}),
        ("mixed", "I look around.", {"scene": "frontier_gate", "not_contains": "rain spatters soot-dark stone"}),
        ("multi", "I follow the missing patrol rumor.", {"scene": "old_milestone"}),
        ("multi", "I examine the weathered milestone.", {"contains": "overlapping prints", "scene": "old_milestone"}),
        ("mixed", "I study the mud prints and look along the track.", {"scene": "old_milestone"}),
        ("multi", "I'll survey the uncertain trail myself.", {"flag": "patrol_survey", "flag_absent": "patrol_report", "scene": "old_milestone"}),
        ("multi", "I write down the limits of the survey.", {"flag": "patrol_survey_recorded", "scene": "old_milestone"}),
        ("progress", "What can I do here?", {"flag": "patrol_survey", "not_contains": "secret rite", "scene": "old_milestone"}),
        ("scene", "If the trail beyond the stone is clear, follow it; otherwise I stay and tell the watch what I saw.", {"not_contains": "rain spatters", "scene": "old_milestone", "flag": "patrol_survey"}),
        ("ordering", "I write down the limits of the survey.", {"duplicate": True, "flag": "patrol_survey_recorded"}),
        ("save", "SAVE", {"flag": "patrol_survey_recorded"}),
    ]
    for _ in range(15):
        http.append(("save", "RESUME", {"flag": "patrol_survey_recorded", "flag_absent": "patrol_report", "scene": "old_milestone"}))
    http.extend([
        ("multi", "I look around the stone again.", {"scene": "old_milestone", "flag": "patrol_survey"}),
        ("isolation", "NEW", {"flag_absent": "patrol_survey"}),
        ("mixed", "I examine the notice board.", {"contains": "northwest mud"}),
        ("multi", "I follow the missing patrol rumor.", {"scene": "old_milestone"}),
        ("multi", "I examine the weathered milestone.", {"contains": "overlapping prints"}),
        ("multi", "I head back and tell the watch the trail is uncertain.", {"flag": "patrol_report", "flag_absent": "patrol_survey"}),
        ("multi", "I return to Cinderwatch Gate.", {"scene": "frontier_gate", "flag": "patrol_report"}),
        ("multi", "I give the watch the patrol report.", {"flag": "patrol_guards_warned"}),
        ("ordering", "I give the watch the patrol report.", {"duplicate": True, "flag": "patrol_guards_warned", "flag_absent": "patrol_survey"}),
        ("save", "SAVE", {"flag": "patrol_guards_warned"}),
        ("save", "RESUME", {"flag": "patrol_guards_warned", "flag_absent": "patrol_survey", "scene": "frontier_gate"}),
        ("scene", "If the trail is clear I would leave, otherwise I stay.", {"not_contains": "rain spatters soot-dark stone", "scene": "frontier_gate"}),
        ("isolation", "I survey the uncertain trail myself.", {"flag_absent": "patrol_survey", "scene": "frontier_gate"}),
        ("progress", "What are my options?", {"not_contains": "secret rite"}),
        ("scene", "I look around the gate.", {"scene": "frontier_gate", "not_contains": "old milestone leans"}),
        ("ordering", "I look around the gate.", {"duplicate": True, "scene": "frontier_gate", "flag": "patrol_guards_warned"}),
        ("multi", "I thank the guard and stay at the gate.", {"scene": "frontier_gate", "flag": "patrol_report"}),
        ("mixed", "I check the notice board and ask who posted the warning.", {"scene": "frontier_gate"}),
        ("speech", "Should I give the watch another report?", {"flag": "patrol_guards_warned", "not_contains": "rain spatters"}),
        ("isolation", "Survey the distant galaxy from the gate.", {"flag_absent": "patrol_survey", "scene": "frontier_gate"}),
    ])
    for lane, text, expect in http:
        cases.append(_case(n, lane=lane, type="http", text=text, expect=expect))
        n += 1
    return cases


def freeze():
    cases = build_cases()
    payload = {
        "cycle": "PR-PLAY-78A",
        "authored_before_run": True,
        "developer_authored": True,
        "external_validation": False,
        "count": len(cases),
        "cases": cases,
    }
    raw = json.dumps(payload, indent=2, ensure_ascii=False)
    MANIFEST.write_text(raw, encoding="utf-8")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    HASH_FILE.write_text(digest + "\n", encoding="utf-8")
    print(json.dumps({"count": len(cases), "hash": digest}))


def _boot(name):
    from tests.helpers.storage_isolation import install
    target = install(OUT / name)
    os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
    os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_BRANCHING"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION"] = "1"
    os.environ["ASHEN_EXPERIMENTAL_DYNAMIC_NPCS"] = "1"
    os.environ["ASHEN_BOUNDED_SPEECH"] = "1"
    return target


def _scene(scene_id, world_flag=None, clues=True, hidden=False, other=False):
    from game.authored_consequences import ENROLLMENT, FIXTURE
    definitions = json.loads(FIXTURE.read_text(encoding="utf-8"))
    actions = json.loads(json.dumps(definitions.get(scene_id, [])))
    if hidden:
        actions.append({
            "id": "secret_rite", "label": "Perform the secret rite", "type": "custom", "hidden": True,
            "conditions": {}, "consequence": {"set_flags": {"secret_rite": True}, "text": "hidden"},
        })
    session = {
        "campaign_run_id": "alpha", "session_id": "alpha", ENROLLMENT: "other" if other else "alpha",
        "active_scene_id": scene_id,
        "clue_knowledge": {},
    }
    if clues:
        session["clue_knowledge"] = {
            "notice_patrol_route": {"state": "discovered", "text": "notice"},
            "milestone_mud_prints": {"state": "discovered", "text": "prints"},
        }
    flags = {}
    if world_flag:
        flags[world_flag] = True
    world = {"world_state": {"flags": flags}, "npcs": []}
    location = "Old Milestone" if scene_id == "old_milestone" else "Cinderwatch Gate"
    scene = {"scene": {
        "id": scene_id, "location": location, "actions": actions,
        "visible_facts": ["Faint overlapping prints mark the mud."], "interactables": [],
    }}
    return session, scene, world


def _prepare(setup):
    table = {
        "ready": ("old_milestone", None, True, False, False),
        "no_clues": ("old_milestone", None, False, False, False),
        "survey_done": ("old_milestone", "patrol_survey", True, False, False),
        "report_done": ("old_milestone", "patrol_report", True, False, False),
        "gate": ("frontier_gate", None, True, False, False),
        "gate_report": ("frontier_gate", "patrol_report", True, False, False),
        "hidden": ("old_milestone", None, True, True, False),
        "other": ("old_milestone", None, True, False, True),
    }
    return _scene(*table[setup])


def _matches(got, expect):
    kind = expect.get("kind")
    if kind == "none":
        return got is None or got.get("kind") != "execute"
    if kind == "not_record":
        return got is None or got.get("kind") != "execute" or got.get("id") == "patrol_survey"
    if not got or got.get("kind") != kind:
        return False
    if expect.get("id") and got.get("id") != expect["id"]:
        return False
    if expect.get("reason") and got.get("reason") != expect["reason"]:
        return False
    message = (got.get("message") or "")
    for word in expect.get("forbids") or []:
        if word.casefold() in message.casefold():
            return False
    return True


def holdout():
    _boot("holdout_data")
    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
    raw = MANIFEST.read_text(encoding="utf-8")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    frozen = HASH_FILE.read_text(encoding="utf-8").strip()
    if digest != frozen:
        raise SystemExit("Holdout manifest hash changed after freeze")
    manifest = json.loads(raw)
    from game.authored_action_language import propose, scene_publication_replacement
    results = []
    http_cases = []
    for case in manifest["cases"]:
        if case["type"] == "http":
            http_cases.append(case)
            continue
        if case["type"] == "scene":
            got = scene_publication_replacement(
                case["text"],
                session={"active_scene_id": case["active"]},
                resolution={"resolved_transition": case["resolved_transition"]},
            )
            ok = bool(got) == bool(case["expect"]["replaced"])
            if ok and got:
                ok = "rain spatters" not in got.casefold() and "still at" in got.casefold()
            results.append({"id": case["id"], "lane": case["lane"], "ok": ok, "replacement": got})
            continue
        session, scene, world = _prepare(case["setup"])
        got = propose(case["text"], scene=scene, world=world, session=session)
        results.append({
            "id": case["id"], "lane": case["lane"], "text": case["text"],
            "ok": _matches(got, case["expect"]),
            "got": None if got is None else {"kind": got.get("kind"), "id": got.get("id"), "reason": got.get("reason")},
            "expect": case["expect"],
        })
    http_results = _http_cases(http_cases)
    results.extend(http_results)
    passed = sum(1 for row in results if row["ok"])
    summary = {
        "hash": digest,
        "count": len(results),
        "passed": passed,
        "failed": [row for row in results if not row["ok"]],
        "lanes": {},
        "multi_turn": sum(1 for row in results if row["lane"] == "multi"),
        "save_resume": sum(1 for row in results if row["lane"] == "save"),
        "mixed": sum(1 for row in results if row["lane"] == "mixed"),
        "scene": sum(1 for row in results if row["lane"] == "scene"),
        "nontrivial_paraphrases": sum(1 for case in manifest["cases"] if case.get("nontrivial")),
        "external_validation": False,
    }
    for row in results:
        summary["lanes"][row["lane"]] = summary["lanes"].get(row["lane"], 0) + 1
    (OUT / "holdout_results.json").write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2)[:4000])


def _http_cases(cases):
    import copy
    from fastapi.testclient import TestClient
    from game import api, storage
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
    api.call_gpt = lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
    api.log_upstream_api_preflight_at_startup = lambda: None
    from tests.test_pr_play_71_lifecycle import create, flags, safe, start
    rows = []
    snap = None
    with TestClient(api.app) as client:
        create(client)
        start(client)
        for case in cases:
            text = case["text"]
            expect = case["expect"]
            before = copy.deepcopy(flags())
            scene_before = storage.load_session().get("active_scene_id")
            if text == "SAVE":
                snap = safe(client.post("/api/snapshots", json={"label": case["id"]}))["snapshot"]["id"]
                payload_text = "snapshot"
            elif text == "RESUME":
                create(client)
                safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
                payload_text = "resumed"
            elif text == "NEW":
                create(client)
                start(client)
                payload_text = storage.load_session().get("active_scene_id") or ""
            else:
                body = {"text": text}
                if expect.get("duplicate"):
                    body["client_request_id"] = "holdout-" + case["id"]
                first = safe(client.post("/api/chat", json=body))
                if expect.get("duplicate"):
                    safe(client.post("/api/chat", json=body))
                payload_text = first["gm_output"]["player_facing_text"]
            ok = True
            scene = storage.load_session().get("active_scene_id")
            if "contains" in expect and expect["contains"].casefold() not in payload_text.casefold():
                ok = False
            if "not_contains" in expect and expect["not_contains"].casefold() in payload_text.casefold():
                ok = False
            if "scene" in expect and scene != expect["scene"]:
                ok = False
            if "flag" in expect and flags().get(expect["flag"]) is not True:
                ok = False
            if "flag_absent" in expect and flags().get(expect["flag_absent"]) is True:
                ok = False
            if text == "NEW" and flags().get("patrol_survey") is True:
                ok = False
            rows.append({
                "id": case["id"], "lane": case["lane"], "text": text, "ok": ok,
                "scene_before": scene_before, "scene": scene,
                "flags": {key: flags().get(key) for key in ("patrol_survey", "patrol_report", "patrol_survey_recorded", "patrol_guards_warned")},
                "player_facing_text": payload_text[:500],
                "unchanged_check": before,
            })
    return rows


def _latency_stats(samples):
    if not samples:
        return {}
    ordered = sorted(samples)
    def pct(p):
        index = min(len(ordered) - 1, max(0, int(round((p / 100) * (len(ordered) - 1)))))
        return ordered[index]
    return {"mean": round(statistics.fmean(samples), 1), "median": round(statistics.median(samples), 1), "p95": round(pct(95), 1), "max": round(max(samples), 1), "n": len(samples)}


def http():
    _boot("http_data")
    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
    import copy
    from fastapi.testclient import TestClient
    from game import api, storage
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
    api.call_gpt = lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
    api.log_upstream_api_preflight_at_startup = lambda: None
    from tests.test_pr_play_71_lifecycle import create, flags, safe, start
    campaigns = {
        "survey": [
            "I examine the notice board.",
            "I follow the missing patrol rumor.",
            "I examine the weathered milestone.",
            "I document what I found beside the milestone.",
            "I write down the limits of the survey.",
            "What can I do here?",
        ],
        "report": [
            "Examine the notice board and ask the guard about the warning.",
            "I follow the missing patrol rumor.",
            "I look at the weathered milestone and the tracks.",
            "I head back and tell the watch the trail is uncertain.",
            "I return to Cinderwatch Gate.",
            "I give the watch the patrol report.",
            "What are my options?",
        ],
    }
    report = {}
    with TestClient(api.app) as client:
        for name, lines in campaigns.items():
            create(client)
            started = start(client)
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
            saved_flags = copy.deepcopy(flags())
            saved_scene = storage.load_session().get("active_scene_id")
            create(client)
            clock = time.perf_counter()
            safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
            samples.append(round((time.perf_counter() - clock) * 1000, 1))
            resumed = chat_state()
            report[name] = {
                "opening": started["gm_output"]["player_facing_text"][:240],
                "turns": turns,
                "snapshot_id": snap,
                "resume_scene": resumed["scene"],
                "resume_flags": resumed["flags"],
                "resume_matches": resumed["scene"] == saved_scene and resumed["flags"] == saved_flags,
                "latency": _latency_stats(samples),
            }
    (OUT / "http_campaigns.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({name: {"resume": row["resume_matches"], "flags": row["resume_flags"], "scene": row["resume_scene"], "latency": row["latency"]} for name, row in report.items()}, indent=2))


def chat_state():
    from game import storage
    from tests.test_pr_play_71_lifecycle import flags
    return {"scene": storage.load_session().get("active_scene_id"), "flags": flags()}


def adaptive():
    _boot("adaptive_data")
    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
    import copy
    from fastapi.testclient import TestClient
    from game import api, storage
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
    api.call_gpt = lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
    api.log_upstream_api_preflight_at_startup = lambda: None
    seen = set()
    rows = []
    samples = []

    def labels_from(payload):
        state = payload.get("public_state") or {}
        ui = payload.get("ui") or state.get("ui") or {}
        names = []
        for item in ui.get("affordances") or []:
            if isinstance(item, dict) and item.get("label"):
                names.append(str(item["label"]))
        return names

    def choose(visible, labels):
        text = " ".join(visible).casefold()
        joined = " ".join(labels).casefold()
        ideas = []
        if "notice" in text or "notice" in joined:
            ideas.append("I examine the notice board.")
        if "mud track" in text or "missing patrol" in text:
            ideas.append("I follow the missing patrol rumor.")
        if "milestone" in text or "milestone" in joined:
            ideas.append("I examine the weathered milestone.")
        if "overlapping prints" in text or "survey the uncertain trail" in joined:
            ideas.append("I'll survey the uncertain trail myself.")
        if "limits of your survey" in text or "record the limits" in joined:
            ideas.append("I write down the limits of the survey.")
        if "bring" in text and "watch" in text:
            ideas.append("I return to Cinderwatch Gate.")
        ideas += [
            "I look around.",
            "I look for signs of a struggle.",
            "I wait and watch the road.",
            "I inspect the ground beside the stone.",
            "Ask the guard what the warning is about.",
            "What can I do here?",
            "I look along the track without leaving.",
            "I check the rainwater at the edge of the path.",
            "Does the marker lean?",
            "I listen for anyone on the road.",
            "What are my options?",
            "I look at the scrub beside the track.",
            "I stay where I am and look back the way I came.",
            "What should I investigate next?",
            "I rest a hand on the stone and look at the mud again.",
            "I count the ruts without stepping off the track.",
            "I look up at the rain and stay put.",
            "I check whether my boots are caked with mud.",
            "I face the way back toward the gate without leaving.",
            "I look for a second set of prints closer to the scrub.",
            "I wait through one more gust of rain.",
            "I keep my voice low and look at the marker.",
            "I study the horizon and remain here.",
        ]
        for idea in ideas:
            if idea not in seen:
                seen.add(idea)
                return idea
        return None

    visible = []
    with TestClient(api.app) as client:
        created = client.post("/api/new_campaign")
        assert created.status_code == 200, created.text
        started = client.post("/api/start_campaign")
        assert started.status_code == 200, started.text
        opening = started.json()
        visible.append(opening["gm_output"]["player_facing_text"])
        labels = labels_from(opening)
        snap = None
        for turn in range(28):
            text = choose(visible, labels)
            if text is None:
                break
            clock = time.perf_counter()
            response = client.post("/api/chat", json={"text": text, "client_request_id": f"adapt-{turn}"})
            elapsed = round((time.perf_counter() - clock) * 1000, 1)
            samples.append(elapsed)
            assert response.status_code == 200, response.text
            payload = response.json()
            facing = payload["gm_output"]["player_facing_text"]
            visible.append(facing)
            labels = labels_from(payload) or labels
            scene = storage.load_session().get("active_scene_id")
            contradiction = scene != "frontier_gate" and "rain spatters soot-dark stone" in facing.casefold()
            rows.append({
                "turn": turn + 1, "input": text, "provenance": "visible-text policy",
                "player_facing_text": facing, "elapsed_ms": elapsed, "scene": scene,
                "labels": labels, "contradiction": contradiction,
                "repeated_observation": facing in {row.get("player_facing_text") for row in rows if row.get("player_facing_text")},
            })
            if turn == 18:
                saved = client.post("/api/snapshots", json={"label": "adaptive"})
                assert saved.status_code == 200, saved.text
                snap = saved.json()["snapshot"]["id"]
                rows.append({"turn": "save", "input": "save", "snapshot": snap, "scene": scene})
            if turn == 19 and snap:
                client.post("/api/new_campaign")
                loaded = client.post("/api/snapshots/load", json={"snapshot_id": snap})
                assert loaded.status_code == 200, loaded.text
                visible.append(loaded.json().get("gm_output", {}).get("player_facing_text") or "resumed")
                rows.append({"turn": "resume", "input": "resume", "scene": storage.load_session().get("active_scene_id")})
        from tests.test_pr_play_71_lifecycle import flags
        end_flags = flags()
        objective = {
            "discovered_patrol": any("northwest mud" in row.get("player_facing_text", "").casefold() for row in rows),
            "investigated_trail": any("overlapping prints" in row.get("player_facing_text", "").casefold() for row in rows),
            "branch": bool(end_flags.get("patrol_survey") or end_flags.get("patrol_report")),
            "consequence": bool(end_flags.get("patrol_survey_recorded") or end_flags.get("patrol_guards_warned")),
            "continued": len([row for row in rows if isinstance(row.get("turn"), int)]) >= 20,
            "save_resume": any(row.get("turn") == "resume" for row in rows) and storage.load_session().get("active_scene_id"),
        }
        meaningful = [row for row in rows if isinstance(row.get("turn"), int)]
        summary = {
            "meaningful_turns": len(meaningful),
            "objective": objective,
            "objective_completed": all(objective.values()),
            "repeated_observations": sum(1 for row in meaningful if row.get("repeated_observation")),
            "contradictions": sum(1 for row in meaningful if row.get("contradiction")),
            "clarifications": sum(1 for row in meaningful if "do you mean" in row["player_facing_text"].casefold()),
            "unsupported": sum(1 for row in meaningful if "not supported" in row["player_facing_text"].casefold() or "cannot be taken" in row["player_facing_text"].casefold()),
            "flags": end_flags,
            "scene": storage.load_session().get("active_scene_id"),
            "latency": _latency_stats(samples),
            "provider_requests": 0,
            "note": "Expression generation and live interpretation were off. The player policy used only visible prose and visible affordance labels, and typed chat.",
        }
    (OUT / "adaptive_play.json").write_text(json.dumps({"summary": summary, "turns": rows}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def provider():
    _boot("provider_data")
    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"
    os.environ["ASHEN_AUTHORED_MATCH_PROVIDER"] = "1"
    os.environ.pop("ASHEN_DISABLE_PROVIDER_CALLS", None)
    import copy
    from fastapi.testclient import TestClient
    from game import api, storage
    from game.authored_action_language import propose, provider_usage
    from game.config import get_openai_api_key
    from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
    try:
        get_openai_api_key()
    except Exception as exc:
        (OUT / "provider_match.json").write_text(json.dumps({"result": "BLOCKED", "reason": str(exc)}), encoding="utf-8")
        print("BLOCKED", exc)
        return
    api.call_gpt = lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
    api.log_upstream_api_preflight_at_startup = lambda: None
    from tests.test_pr_play_71_lifecycle import create, flags, reach, safe, start
    utterance = "The watch ought to hear about those uncertain marks."
    with TestClient(api.app) as client:
        create(client)
        start(client)
        reach(client)
        before = copy.deepcopy(flags())
        scene = storage.load_active_scene()
        session = storage.load_session()
        world = storage.load_world()
        os.environ["ASHEN_AUTHORED_MATCH_PROVIDER"] = "0"
        deterministic = propose(utterance, scene=scene, world=world, session=session)
        os.environ["ASHEN_AUTHORED_MATCH_PROVIDER"] = "1"
        clock = time.perf_counter()
        try:
            payload = safe(client.post("/api/chat", json={"text": utterance, "client_request_id": "provider-match"}))
        except Exception as exc:
            (OUT / "provider_match.json").write_text(json.dumps({"result": "BLOCKED", "reason": str(exc), "deterministic": None if deterministic is None else deterministic.get("kind")}, indent=2), encoding="utf-8")
            print("BLOCKED", exc)
            return
        elapsed = round((time.perf_counter() - clock) * 1000, 1)
        after = copy.deepcopy(flags())
        snap = safe(client.post("/api/snapshots", json={"label": "provider"}))["snapshot"]["id"]
        create(client)
        safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
        resumed = flags().get("patrol_report") is True
    record = {
        "result": "ACCEPTED" if after.get("patrol_report") is True and before.get("patrol_report") is not True else "REJECTED",
        "utterance": utterance,
        "deterministic_without_provider": None if deterministic is None else {"kind": deterministic.get("kind"), "id": deterministic.get("id")},
        "before": before,
        "after": after,
        "resume_preserved_report": resumed,
        "player_facing_text": payload["gm_output"]["player_facing_text"],
        "elapsed_ms": elapsed,
        "usage": provider_usage(),
        "scene": storage.load_session().get("active_scene_id"),
    }
    (OUT / "provider_match.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({key: record[key] for key in ("result", "deterministic_without_provider", "after", "resume_preserved_report", "elapsed_ms", "usage")}, indent=2))


def hashes():
    before = json.loads((ROOT / "artifacts" / "pr_play_78" / "protected_before.json").read_text(encoding="utf-8"))
    mismatches = []
    missing = []
    for row in before["files"]:
        path = ROOT / row["path"]
        if not path.exists():
            missing.append(row["path"])
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row["sha256"] or path.stat().st_size != row["bytes"]:
            mismatches.append({"path": row["path"], "expected": row["sha256"], "actual": digest})
    result = {"expected": before["count"], "preserved": before["count"] - len(mismatches) - len(missing), "mismatches": mismatches, "missing": missing}
    (OUT / "protected_hashes.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


def devcount():
    import subprocess
    log = OUT / "devtests.txt"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_pr_play_78a_authored.py", "tests/test_pr_play_78_integrated.py", "tests/test_pr_play_72_boundary_repairs.py", "-q", "--tb=line"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    log.write_text(result.stdout, encoding="utf-8")
    print(result.stdout[-1500:])
    print("exit", result.returncode)


if __name__ == "__main__":
    command = sys.argv[1]
    {"freeze": freeze, "holdout": holdout, "http": http, "adaptive": adaptive, "provider": provider, "hashes": hashes, "devcount": devcount}[command]()
