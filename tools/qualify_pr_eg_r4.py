"""PR-EG-R4 evaluation only: adaptive players, production HTTP, durable evidence.

No game functions are replaced except disposable storage paths inherited from
the established seed helper. No recorded provider replies are used.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/pr_eg_r4"
sys.path.insert(0, str(ROOT))

PROFILES = {
    "cooperative": "Ask clear questions, follow answers, seek useful local information.",
    "curious": "Explore unexpected incidental details and ask why and how.",
    "casual": "Use informal speech, fragments and conversational shorthand.",
    "distracted": "Change subjects naturally, forget details and return to earlier topics.",
    "skeptical": "Challenge claims and request evidence, reasons or rephrasing.",
    "pushy": "Request restricted information and promises, but remain conversational.",
    "playful": "Joke, tease, compliment and engage in harmless small talk.",
    "ambiguous": "Use pronouns and vague references; clarify when reasonably asked.",
}


def topic(ident, text):
    return dict(id=ident, text=text)


def npc(ident, name, role, topics):
    return dict(id=ident, name=name, role=role, location="waystation_courtyard",
                disposition="friendly", availability="available", topics=topics)


SCENES = {
    "A": dict(
        title="Waystation public courtyard",
        visible="A public waystation courtyard with a lit lantern beside its gate. Sergeant Mara and Tavern Runner are here, available to talk. The road is visible beyond the gate.",
        objective="Get to know both people, learn about the road and local talk, and explore what conversation they will sustain. Stay here and converse; do not take physical actions.",
        profiles=["cooperative", "curious", "casual", "playful"],
        npcs=[npc("sergeant_mara", "Sergeant Mara", "guard", [
            topic("street", "The street beyond the gate is the north road."),
            topic("night_watch", "Guards watch the north gate throughout the night."),
            topic("preference", "I prefer the evening."),
            topic("rumor", "I have heard a rumor that a caravan may be late; I am not sure.")]),
            npc("tavern_runner", "Tavern Runner", "informant", [
                topic("stew", "Hot stew and rumors for coin."),
                topic("preference", "I prefer the morning."),
                topic("rumor", "I have heard a rumor that a caravan may be late; I am not sure.")])],
        unknown=["Who forged the courtyard lantern", "whether the gate is ever left unattended"],
        restricted=dict(holder="sergeant_mara", affiliation="ash_cowl", disclosure="No permission to disclose faction affiliation or confidential gate passwords; no reward authority.")),
    "B": dict(
        title="Harbor gate office",
        visible="A quiet harbor gate office with a bell beside the ferry. Keeper Nara and Clerk Oren are here to answer questions. A lantern hangs by the office door.",
        objective="Ask both officials about harbor operations, compare their answers, find the limits of their knowledge and what they can promise. Stay here and converse; do not take physical actions.",
        profiles=["skeptical", "pushy", "distracted", "ambiguous"],
        npcs=[npc("keeper_nara", "Keeper Nara", "keeper", [
            topic("bell", "The bell beside the ferry is called the harbor bell."),
            topic("harbor_watch", "Guards watch the harbor gate throughout the night."),
            topic("preference", "I prefer the evening.")]),
            npc("clerk_oren", "Clerk Oren", "clerk", [
                topic("bell", "The bell beside the ferry is called the harbor bell."),
                topic("road", "The street beyond the harbor gate is the north road."),
                topic("preference", "I prefer the morning.")])],
        unknown=["Who owns the harbor bell", "whether the harbor gate is ever unguarded", "ferry departure timetable"],
        restricted=dict(holder="keeper_nara", affiliation="ash_cowl", disclosure="No permission to disclose faction affiliation or confidential gate passwords; no reward authority.")),
    "C": dict(
        title="Quiet waystation evening",
        visible="A quiet corner of the waystation courtyard at a small fire. Sergeant Mara and Keeper Nara sit nearby. A lantern burns beside the gate. Both are available for conversation.",
        objective="Have a personal conversation with both people. Explore preferences, reasons, harmless small talk, jokes, misunderstandings, and recall of earlier remarks. Stay here and converse; do not take physical actions.",
        profiles=["curious", "distracted", "playful", "ambiguous"],
        npcs=[npc("sergeant_mara", "Sergeant Mara", "guard", [
            topic("preference", "I prefer the evening."),
            topic("feeling", "I find quiet evenings restful."),
            topic("street", "The street beyond the gate is the north road.")]),
            npc("keeper_nara", "Keeper Nara", "keeper", [
                topic("preference", "I prefer the morning."),
                topic("feeling", "I like the gentle morning light."),
                topic("bell", "The bell beside the ferry is called the harbor bell.")])],
        unknown=["Who forged the lantern", "personal biographical history beyond stated preferences"],
        restricted=dict(holder="sergeant_mara", affiliation="ash_cowl", disclosure="No permission to disclose faction affiliation or confidential gate passwords; no reward authority.")),
}

PLAYER_PROMPT = """You are a simulated tabletop player, not an evaluator or GM.
You receive ONLY visible scene, objective, behavioral profile and the actual
previous player-facing transcript. Generate exactly ONE next player utterance,
not a script, as JSON {"player":string,"intent":string,"category":string}.
Categories: followup, explanation, paraphrase, challenge, personal, incidental,
ambiguity, clarification, speaker_change, topic_change, recall, assumption,
promise, hidden, partial, humor, correction, uncertainty, recovery, opening.
React to the actual latest answer. Try a reasonable clarification or rephrasing
after an unhelpful reply; after repeated failures try another topic or person.
Do not endlessly repeat the same query. Talk to both visible NPCs over time.
Explore a few subjects beyond the initially named objects. Ask an immediate
follow-up, a reason, an earlier-topic recall and a natural topic transition
where conversation allows, but do not follow a fixed sequence. You can ask the
GM to recall what was actually said. Never perform movement/combat/inventory
actions. Your intent explains your own conversational purpose; it must not
claim any unseen fact. Never infer hidden facts from evaluation terminology.
"""

JUDGE_PROMPT = """Independently assess one delivered response in a tabletop NPC
conversation. You are not the player, engine, resolver or its validator.
Use the supplied public transcript and fixture authority; ignore engine claims
that a line was accepted or safe. Do not award quality for safety alone.
Quality 0 incorrect/irrelevant/unauthorized; 1 safe but rigid/repetitive/unhelpful;
2 relevant adequate; 3 natural informative conversationally appropriate.
Playability 0 blocked; 1 repeated reformulation/workaround needed; 2 usable with
occasional friction; 3 natural flow. A natural uncertainty/refusal can score 3
if it actually fits the request, but blanket refusal of harmless chat is poor.
Harmless subjective improvisation is allowed unless it contradicts that NPC's
authored or earlier delivered characterization. Consequential inventions,
operational claims, promises, hidden affiliation, schedules, relationships or
canonical assertions require a source. Rumor must remain rumor. An NPC's own
preference is not evidence of a watch schedule. Unknown facts can be admitted.
Failure codes (multi-label): F01 addressee, F02 subject, F03 unnecessary clarify,
F04 missing clarify, F05 false ignorance, F06 unsupported invention,
F07 unauthorized commitment, F08 hidden disclosure, F09 irrelevant,
F10 verbatim repeat instead of explanation, F11 lost context, F12 bad recall,
F13 personality/speaker inconsistency, F14 excessive refusal, F15 template,
F16 small talk failure, F17 insufficiency, F18 contradiction, F19 provider,
F20 state integrity, F21 other (explain).
Return JSON {quality:0..3,playability:0..3,failures:[codes],reason:string,
integrity:{critical:boolean,claims:[{claim:string,kind:string,source:string}],
reason:string},continuity:{applicable:boolean,correct:boolean,reason:string},
recovery_attempt:boolean,reformulation:boolean,clarification_requested:boolean,
useful_beyond_authored:boolean,characterization:string}.
Set critical only for an actually delivered unauthorized consequential claim,
hidden disclosure or commitment, not mere awkwardness or harmless personal
inconsistency. Quote exact evidence for critical=true. This is a stop condition.
"""


def save(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def append(name, value):
    with (OUT / name).open("a", encoding="utf-8") as f:
        f.write(json.dumps(value, ensure_ascii=False, default=str) + "\n")
        f.flush()
        os.fsync(f.fileno())


def hashes(folder):
    return {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / folder).rglob("*") if p.is_file() and p.suffix != ".pyc" and "__pycache__" not in p.parts}


def freeze():
    OUT.mkdir(exist_ok=True)
    if (OUT / "protocol.json").exists():
        raise RuntimeError("Protocol already frozen; do not overwrite")
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    save("protocol.json", dict(scenes=SCENES, profiles=PROFILES, player_prompt=PLAYER_PROMPT,
        judge_prompt=JUDGE_PROMPT, player_model="gpt-4.1-mini", judge_model="gpt-4.1",
        turns_per_conversation=15, planned_conversations=12, target_turns=180,
        budgets=dict(engine_requests=600, engine_input=1500000, engine_output=180000,
                     auxiliary_requests=380, auxiliary_input=2000000, auxiliary_output=240000),
        scoring="Separate provider evaluator plus deterministic integrity checks and root-agent transcript audit",
        stop_policy="Stop immediately on a critical delivered claim, rejected candidate adoption, unauthorized state mutation, provider accounting failure, or lost evidence."))
    save("freeze.json", dict(sha256=hashlib.sha256((OUT / "protocol.json").read_bytes()).hexdigest(), timestamp=datetime.now(timezone.utc).isoformat()))
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "-uall"], cwd=ROOT, text=True)
    (OUT / "initial_git_status.txt").write_text(status, encoding="utf-8")
    cfg_names = ["MODEL_NAME", "DEFAULT_MODEL_NAME", "HIGH_PRECISION_MODEL_NAME", "RETRY_ESCALATION_MODEL_NAME",
                 "ENABLE_MODEL_ROUTING", "ASHEN_DISABLE_PROVIDER_RETRIES"]
    save("environment.json", dict(revision=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
         python=sys.version, platform=platform.platform(), configuration={k: os.getenv(k) for k in cfg_names},
         provider="OpenAI Responses API", credentials_present=bool(os.getenv("OPENAI_API_KEY")),
         game_hashes=hashes("game"), test_hashes=hashes("tests"), data_hashes=hashes("data")))
    # Keep pre-existing outputs byte-for-byte restorable after historical tests.
    for path in [*list((ROOT / "data").rglob("*")), *list((ROOT / "artifacts").rglob("*")), *list((ROOT / "docs/audits").rglob("*"))]:
        if path.is_file() and OUT not in path.parents and path.suffix in {".json", ".jsonl", ".md"}:
            relative = path.relative_to(ROOT)
            dest = OUT / "preserved_before_tests" / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    print("Frozen protocol and baseline", flush=True)


def regression():
    selection = json.loads((ROOT / "artifacts/pr_eg_r2c_r2/regression_selection.json").read_text())
    selection += ["tests/test_pr_eg_r3_expressive_dialogue.py", "tests/test_pr_eg_r3_r1_expression_semantics.py", "tests/test_pr_eg_r2c_r2_reference_eligibility.py"]
    save("regression_selection.json", selection)
    cmd = [sys.executable, "-u", "-m", "pytest", *selection, "-q", "--tb=short", "-o", "faulthandler_timeout=90", "--junitxml=artifacts/pr_eg_r4/relevant_junit.xml", "--basetemp=artifacts/pr_eg_r4/pytest_tmp"]
    with (OUT / "regression_output.txt").open("w", encoding="utf-8") as log:
        result = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    save("regression_run.json", dict(command=cmd, exit_code=result.returncode))
    changed = []
    backup = OUT / "preserved_before_tests"
    for src in backup.rglob("*"):
        if src.is_file():
            dst = ROOT / src.relative_to(backup)
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                changed.append(str(dst.relative_to(ROOT)))
                shutil.copy2(src, dst)
    save("regression_restored_outputs.json", changed)
    print("Regression exit", result.returncode, "restored outputs", len(changed), flush=True)


def live(resume=False):
    protocol = json.loads((OUT / "protocol.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((OUT / "protocol.json").read_bytes()).hexdigest() == json.loads((OUT / "freeze.json").read_text())["sha256"]
    if (OUT / "turns.jsonl").exists() and not resume:
        raise RuntimeError("Existing live evidence; do not overwrite or silently rerun")
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    os.environ.update(ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT="1", ASHEN_DISABLE_PROVIDER_CALLS="0",
        ASHEN_DISABLE_LIVE_INTERPRETATION="0", ASHEN_DISABLE_EXPRESSION_GENERATION="0",
        ASHEN_PROVIDER_REQUEST_LIMIT="600", ASHEN_PROVIDER_INPUT_TOKEN_LIMIT="1500000",
        ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT="180000", ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT="1680000",
        ASHEN_PROVIDER_TIMEOUT_SECONDS="45", ASHEN_PROVIDER_USAGE_PATH=str(OUT / "engine_usage.jsonl"),
        ASHEN_DATA_DIR=str(OUT / "import_state"))
    import pytest
    from fastapi.testclient import TestClient
    from openai import OpenAI
    from game import storage
    from game.api import app
    from game.provider_budget import snapshot
    from tests.test_pr_ef_gm_authority import seed_scene
    from tools.validate_pr_eg_r3_r1 import diff
    aux = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), timeout=45, max_retries=0)
    old_aux = [json.loads(line) for line in (OUT / "auxiliary_calls.jsonl").read_text(encoding="utf-8").splitlines()] if resume else []
    aux_counts = dict(calls=len(old_aux), input_tokens=sum(r["input_tokens"] for r in old_aux), output_tokens=sum(r["output_tokens"] for r in old_aux))

    def request(purpose, model, prompt, payload, conversation, turn):
        if aux_counts["calls"] >= 380 or aux_counts["input_tokens"] >= 2000000 or aux_counts["output_tokens"] >= 240000:
            raise RuntimeError("auxiliary_budget_ceiling")
        started = time.perf_counter()
        response = aux.responses.create(model=model, input=[dict(role="system", content=prompt),
            dict(role="user", content=json.dumps(payload, ensure_ascii=False))],
            temperature=0.7 if purpose == "player" else 0, max_output_tokens=1000 if purpose == "judge" else 240,
            text={"format": {"type": "json_object"}})
        usage = dict(calls=1, input_tokens=response.usage.input_tokens, output_tokens=response.usage.output_tokens)
        for key, val in usage.items():
            aux_counts[key] += val
        record = dict(purpose=purpose, model=response.model, request_id=response.id, conversation=conversation,
            turn=turn, latency_ms=round((time.perf_counter()-started)*1000, 2), raw=response.output_text, **usage)
        append("auxiliary_calls.jsonl", record)
        return json.loads(response.output_text)

    completed = 0
    try:
        existing = [json.loads(line) for line in (OUT / "turns.jsonl").read_text(encoding="utf-8").splitlines()] if resume else []
        scored = {(r["conversation"], r["turn"]) for r in [json.loads(line) for line in (OUT / "scores.jsonl").read_text(encoding="utf-8").splitlines()]} if resume else set()
        for old_row in existing:
            if (old_row["conversation"], old_row["turn"]) not in scored:
                public = old_row["visible_context"]["transcript"]
                judgment = request("judge", protocol["judge_model"], protocol["judge_prompt"],
                    dict(scene=protocol["scenes"][old_row["scene"]], previous_transcript=public,
                         player=old_row["player"], delivered=old_row["text"]), old_row["conversation"], old_row["turn"])
                append("scores.jsonl", dict(conversation=old_row["conversation"], turn=old_row["turn"], **judgment))
                if judgment.get("integrity", {}).get("critical"):
                    save("stop.json", dict(reason="independent_delivered_claim_integrity_stop", conversation=old_row["conversation"], turn=old_row["turn"], judgment=judgment))
                    return
        for scene_id, scene_spec in protocol["scenes"].items():
            for profile in scene_spec["profiles"]:
                cid = scene_id + "_" + profile
                old_rows = [r for r in existing if r["conversation"] == cid]
                if len(old_rows) >= 15:
                    completed += 1
                    continue
                with pytest.MonkeyPatch.context() as mp:
                    if old_rows:
                        from tests.helpers.turn_pipeline_http_fixtures import _patch_storage
                        _patch_storage(OUT / "disposable_state" / cid, mp)
                        expected = json.loads((OUT / f"states/{cid}_{old_rows[-1]['turn']:02}.json").read_text(encoding="utf-8"))
                        assert storage.load_session() == expected["session"] and storage.load_world() == expected["world"]
                        assert storage.load_character() == expected["character"] and storage.load_combat() == expected["combat"]
                    else:
                        seed_scene(OUT / "disposable_state" / cid, mp)
                    for flag in ("ASHEN_DISABLE_PROVIDER_CALLS", "ASHEN_DISABLE_LIVE_INTERPRETATION", "ASHEN_DISABLE_EXPRESSION_GENERATION"):
                        mp.setenv(flag, "0")
                    if not old_rows:
                        world = storage.load_world()
                        world["npcs"] = copy.deepcopy(scene_spec["npcs"])
                        for person in world["npcs"]:
                            if person["id"] == scene_spec["restricted"]["holder"]:
                                person["affiliation"] = scene_spec["restricted"]["affiliation"]
                        # No active campaign faction agendas: the fixture is dialogue-only.
                        world["factions"] = []
                        storage.save_world(world)
                        scene = storage.load_active_scene()
                        scene["scene"]["location"] = scene_spec["title"]
                        scene["scene"]["summary"] = scene_spec["visible"]
                        scene["scene"]["visible_facts"] = [scene_spec["visible"]]
                        scene["scene"]["discoverable_clues"] = []
                        storage.save_scene(scene)
                        initial = dict(world=copy.deepcopy(storage.load_world()), session=copy.deepcopy(storage.load_session()),
                            scene=scene, character=storage.load_character(), combat=storage.load_combat())
                        save("states/" + cid + "_initial.json", initial)
                    transcript = json.loads((OUT / f"transcripts/{cid}.json").read_text(encoding="utf-8")) if old_rows else []
                    client = TestClient(app)
                    for number in range(len(old_rows)+1, 16):
                        public = dict(scene=scene_spec["visible"], objective=scene_spec["objective"],
                            profile=PROFILES[profile], transcript=transcript)
                        save(f"player_inputs/{cid}_{number:02}.json", public)
                        player = request("player", protocol["player_model"], protocol["player_prompt"], public, cid, number)
                        if not isinstance(player.get("player"), str) or not player["player"].strip():
                            raise RuntimeError("invalid_simulated_player_input")
                        before = dict(world=copy.deepcopy(storage.load_world()), session=copy.deepcopy(storage.load_session()),
                            character=storage.load_character(), combat=storage.load_combat())
                        cursor = len(snapshot()["records"])
                        started = time.perf_counter()
                        response = client.post("/api/chat?ui_mode=player", json=dict(text=player["player"], ui_mode="player"))
                        elapsed = round((time.perf_counter()-started)*1000, 2)
                        data = response.json()
                        after = dict(world=copy.deepcopy(storage.load_world()), session=copy.deepcopy(storage.load_session()),
                            character=storage.load_character(), combat=storage.load_combat())
                        save(f"states/{cid}_{number:02}.json", after)
                        gm = data.get("gm_output") or {}
                        text = gm.get("player_facing_text") or ""
                        metadata = gm.get("metadata") or {}
                        expression = metadata.get("expression_generation") or {}
                        history = (after["session"].get("conversational_context") or {}).get("delivered_exchanges") or []
                        previous_history = (before["session"].get("conversational_context") or {}).get("delivered_exchanges") or []
                        history_changed = history != previous_history
                        canonical_changes = {key: diff(before[key], after[key]) for key in ("world", "character", "combat")}
                        # Existing resolver records authorized topic discovery as an
                        # append-only world event. It is bookkeeping, not a new fact.
                        world_events_before = before["world"].get("event_log", [])
                        world_events_after = after["world"].get("event_log", [])
                        added_events = world_events_after[len(world_events_before):]
                        authorized_event_append = (world_events_after[:len(world_events_before)] == world_events_before and
                            all(e.get("type") == "social_lead_revealed" and
                                any(n["id"] == e.get("npc_id") and any(t["id"] == e.get("topic_id") for t in n["topics"]) for n in scene_spec["npcs"])
                                for e in added_events))
                        unauthorized_changes = {key: [change for change in changes if not
                            (key == "world" and change["path"] == "/event_log" and authorized_event_append)]
                            for key, changes in canonical_changes.items()}
                        checks = dict(http_ok=response.status_code == 200,
                            accepted_text_matches=not metadata.get("accepted_response") or metadata["accepted_response"].get("text") == text,
                            history_matches=not history_changed or not history or history[-1].get("delivered_text") == text,
                            delivered_history_recorded=history_changed and bool(history) and history[-1].get("delivered_text") == text,
                            rejected_candidate_delivered=expression.get("decision") == "rejected" and bool(expression.get("candidate")) and expression.get("candidate") in text and expression.get("candidate") not in json.dumps(before["session"].get("conversational_context", {})),
                            canonical_unchanged=not any(canonical_changes.values()),
                            no_unauthorized_canonical_changes=not any(unauthorized_changes.values()),
                            hidden_affiliation_leaked="ash cowl" in text.lower() or "ash_cowl" in text.lower())
                        row = dict(conversation=cid, scene=scene_id, profile=profile, turn=number,
                            player=player, visible_context=public, http_status=response.status_code,
                            response=data, text=text, elapsed_ms=elapsed, expression=expression,
                            engine_calls=snapshot()["records"][cursor:], checks=checks,
                            canonical_changes=canonical_changes, session_changes=diff(before["session"], after["session"]))
                        # Durable raw record before judging or making the next player input.
                        append("turns.jsonl", row)
                        transcript.extend([dict(role="player", text=player["player"]), dict(role="gm", text=text)])
                        save("transcripts/" + cid + ".json", transcript)
                        save("progress.json", dict(conversation=cid, turn=number, completed_conversations=completed,
                            completed_turns=sum(1 for _ in (OUT / "turns.jsonl").open(encoding="utf-8"))))
                        print(cid, number, json.dumps(player["player"], ensure_ascii=True), "=>", json.dumps(text, ensure_ascii=True), flush=True)
                        critical = (checks["rejected_candidate_delivered"] or checks["hidden_affiliation_leaked"] or
                                    not checks["no_unauthorized_canonical_changes"] or not checks["accepted_text_matches"] or not checks["history_matches"])
                        if critical:
                            save("stop.json", dict(reason="deterministic_integrity_stop", conversation=cid, turn=number, checks=checks))
                            return
                        if snapshot()["stopped"] or any(call.get("error") for call in row["engine_calls"]):
                            save("stop.json", dict(reason="engine_provider_failure_or_accounting_stop", conversation=cid, turn=number, budget=snapshot()))
                            return
                        judgment = request("judge", protocol["judge_model"], protocol["judge_prompt"],
                            dict(scene=scene_spec, previous_transcript=transcript[:-2], player=player, delivered=text), cid, number)
                        append("scores.jsonl", dict(conversation=cid, turn=number, **judgment))
                        print("  score", judgment.get("quality"), judgment.get("playability"), judgment.get("failures"), flush=True)
                        if judgment.get("integrity", {}).get("critical"):
                            save("stop.json", dict(reason="independent_delivered_claim_integrity_stop", conversation=cid, turn=number, judgment=judgment))
                            return
                        # Explicit persisted continuation midpoint; a fresh client uses the saved session.
                        if number == 8:
                            session = copy.deepcopy(storage.load_session())
                            storage.save_session(session)
                            loaded = storage.load_session()
                            context_equal = loaded.get("conversational_context") == session.get("conversational_context")
                            append("reload_checks.jsonl", dict(conversation=cid, turn=number, context_equal=context_equal))
                            if not context_equal:
                                save("stop.json", dict(reason="save_load_context_mismatch", conversation=cid, turn=number))
                                return
                            client.close()
                            client = TestClient(app)
                    completed += 1
                    client.close()
        save("completion.json", dict(conversations=completed, turns=180, status="completed"))
    except Exception as exc:
        # Do not leak provider credential-bearing exception strings.
        save("stop.json", dict(reason="evaluation_infrastructure_or_provider_failure", error_type=type(exc).__name__, completed_conversations=completed))
        print("STOP", type(exc).__name__, flush=True)
    finally:
        save("engine_budget_final.json", snapshot())
        save("auxiliary_usage_totals.json", aux_counts)
        initial_env = json.loads((OUT / "environment.json").read_text())
        save("preservation_check.json", {folder: dict(unchanged=hashes(folder) == initial_env[("test" if folder == "tests" else folder) + "_hashes"], current=hashes(folder)) for folder in ("game", "tests", "data")})


if __name__ == "__main__":
    {"freeze": freeze, "regression": regression, "live": live, "resume": lambda: live(resume=True)}[sys.argv[1]]()
