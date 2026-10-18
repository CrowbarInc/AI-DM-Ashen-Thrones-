"""PR-EF-R4 fresh-provider qualification through production /api/chat.

Disposable campaign only. Does not print secrets. Does not rewrite frozen holdouts.
"""
from __future__ import annotations

import copy
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "pr_ef_r4"
sys.path.insert(0, str(ROOT))

_SECRET = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")


def scrub(value):
    text = json.dumps(value, ensure_ascii=False, default=str)
    return json.loads(_SECRET.sub("[redacted]", text))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    usage_path = OUT / "live.usage.jsonl"
    if usage_path.exists():
        usage_path.unlink()
    os.environ.update(
        ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT="1",
        ASHEN_DISABLE_PROVIDER_CALLS="0",
        ASHEN_DISABLE_LIVE_INTERPRETATION="0",
        ASHEN_PROVIDER_REQUEST_LIMIT="160",
        ASHEN_PROVIDER_INPUT_TOKEN_LIMIT="2500000",
        ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT="80000",
        ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT="2600000",
        ASHEN_PROVIDER_TIMEOUT_SECONDS="45",
        ASHEN_NARRATION_MAX_OUTPUT_TOKENS="1600",
        ASHEN_PROVIDER_USAGE_PATH=str(usage_path),
    )
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    if not os.environ.get("OPENAI_API_KEY"):
        (OUT / "live_status.json").write_text(
            json.dumps({"status": "UNVERIFIED", "reason": "OPENAI_API_KEY is not configured"}, indent=2),
            encoding="utf-8",
        )
        print(json.dumps({"status": "UNVERIFIED", "reason": "key_missing"}), flush=True)
        return

    import pytest
    from fastapi.testclient import TestClient

    from game import storage
    from game.api import app
    from game.provider_budget import snapshot
    from tests.test_pr_ef_gm_authority import seed_scene
    from tests.test_pr_ef_r4_authorization import HOLDOUTS, _add_bren, _integrity, _mutated, _prepare

    # Package imports used by the disposable world force interpretation off. Turn it back on.
    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"

    conversation = [
        ("Could you describe our surroundings?", "gm_no_mutation"),
        ("I ask Sergeant Mara whether the north road is watched.", "execute_mara"),
        ("What did you mean by the north road?", "execute_mara"),
        ("What did she mean by the road?", "gm_no_mutation"),
        ("I ask one of them what happened.", "clarify_no_mutation"),
        ("The sergeant.", "execute_mara"),
        ("Instead, make that a question about the lamp.", "cannot_undo"),
        ("I inspect the courtyard lantern.", "inspect"),
        ("Does the gate look safe? If so, I go through.", "no_move"),
        ("I walk through the courtyard gate.", "move_street"),
    ]
    labels = {
        "explicit_named_ask": ("NPC", "QUESTION"),
        "explicit_role_ask": ("NPC", "QUESTION"),
        "unique_pronoun": ("NPC", "QUESTION"),
        "gm_about_npc": ("GM", "QUESTION"),
        "direct_ask_conflicting_owner": ("NPC", "QUESTION"),
        "npc_followup": ("NPC", "QUESTION"),
        "gm_clarification_of_npc": ("GM", None),
        "correction_pending": (None, "CORRECTION"),
        "correction_already_executed": (None, "CORRECTION"),
        "correction_nothing_pending": (None, "CORRECTION"),
        "confirm_single_candidate": (None, "CONFIRMATION"),
        "confirm_without_proposal": (None, "CONFIRMATION"),
        "confirm_among_many": (None, "CONFIRMATION"),
        "withdrawal": (None, "WITHDRAWAL"),
        "incidental_glance": ("NPC", "QUESTION"),
    }

    def compact(session, world):
        row = _integrity(session, world)
        row.pop("world", None)
        character = storage.load_character()
        row["character_location"] = (character or {}).get("location") or (character or {}).get("current_scene_id")
        row["relationships"] = copy.deepcopy((session or {}).get("relationships") or (world or {}).get("relationships"))
        return row

    def turn_records(start_index: int):
        records = snapshot().get("records") or []
        return records[start_index:]

    def summarize_calls(records):
        def count(purpose):
            return sum(1 for row in records if row.get("sent") and row.get("purpose") == purpose)

        sent = [row for row in records if row.get("sent")]
        return {
            "provider_calls": len(sent),
            "interpretation_calls": count("interpretation"),
            "narration_calls": sum(1 for row in sent if row.get("purpose") not in {"interpretation", "retry_escalation"}),
            "retry_calls": count("retry_escalation"),
            "input_tokens": sum(int(row.get("input_tokens") or 0) for row in sent),
            "output_tokens": sum(int(row.get("output_tokens") or 0) for row in sent),
            "total_tokens": sum(int(row.get("total_tokens") or 0) for row in sent),
            "purposes": [row.get("purpose") for row in sent],
        }

    def score_behavior(expect, data, before, after, text):
        resolution = data.get("resolution") or {}
        social = resolution.get("social") or {}
        lowered = text.lower()
        mutated = (
            before.get("turn_counter") != after.get("turn_counter")
            or before.get("clocks") != after.get("clocks")
            or before.get("factions") != after.get("factions")
            or before.get("scene") != after.get("scene")
        )
        if expect == "execute_mara":
            ok = social.get("npc_id") == "sergeant_mara" and social.get("target_resolved") is True and "cannot be identified" not in lowered
        elif expect == "gm_no_mutation":
            ok = not social and not mutated and "says," not in lowered
        elif expect == "clarify_no_mutation":
            ok = not social and not mutated
        elif expect == "cannot_undo":
            ok = not social and not mutated and ("cannot undo" in lowered or "already resolved" in lowered)
        elif expect == "inspect":
            ok = resolution.get("kind") in {"discover_clue", "inspect", "examine"} or resolution.get("action_id") == "courtyard_lantern" or "maker" in lowered
        elif expect == "no_move":
            ok = after.get("scene") == before.get("scene") and not social
        elif expect == "move_street":
            ok = after.get("scene") == "waystation_street"
        else:
            ok = False
        return bool(ok), mutated

    def score_holdout(case, data, before, after):
        resolution = data.get("resolution") or {}
        social = resolution.get("social") or {}
        text = (data.get("gm_output") or {}).get("player_facing_text") or ""
        lowered = text.lower()
        expect = case["expect"]
        mutated = _mutated(before, after)
        behavior = False
        if expect == "execute_npc":
            behavior = social.get("npc_id") == case["target"] and social.get("target_resolved") is True and "cannot be identified" not in lowered
        elif expect == "clarify_no_mutation":
            behavior = not social and not mutated and (
                "nothing has been attempted" in lowered
                or "has been attempted" in lowered
                or "which person" in lowered
                or "who are you asking" in lowered
                or "yes does not choose" in lowered
                or "what are you trying" in lowered
                or "does not confirm" in lowered
                or "what do you want to change" in lowered
            )
        elif expect == "gm_no_social":
            behavior = not social and not mutated and "says," not in lowered and "its cause has not been established" not in lowered
        elif expect == "revise_no_execution":
            pending = (storage.load_session().get("conversational_context") or {}).get("pending_intention") or {}
            behavior = not social and not mutated and "revised" in lowered and pending.get("status") == "pending"
        elif expect == "cannot_undo":
            behavior = not social and not mutated and "cannot undo" in lowered
        elif expect == "ask_what_to_change":
            behavior = not social and not mutated and "what do you want to change" in lowered and "lantern" not in lowered
        elif expect == "withdraw_no_execution":
            pending = (storage.load_session().get("conversational_context") or {}).get("pending_intention")
            behavior = not social and not mutated and pending in (None, {})
        elif expect == "preserve_both_no_flatten":
            behavior = not social and after.get("scene") == before.get("scene") and not mutated and "ask" in lowered and "leave" in lowered
        elif expect == "execute_after_reload":
            behavior = social.get("npc_id") == case["target"]
        record = (((data.get("resolution") or {}).get("metadata") or {}).get("live_chat_interpretation") or {}).get("record") or {}
        communication = record.get("communication") if isinstance(record, dict) else {}
        expected_label = labels.get(case["id"])
        if expected_label:
            recipient, purpose = expected_label
            actual_recipient = (communication or {}).get("recipient")
            actual_purpose = (communication or {}).get("purpose")
            label_pass = (recipient is None or actual_recipient == recipient) and (purpose is None or actual_purpose == purpose)
        else:
            label_pass = None
        decision = ((data.get("resolution") or {}).get("metadata") or {}).get("conversational_decision") or {}
        contract = ((data.get("resolution") or {}).get("metadata") or {}).get("resolution_contract") or {}
        authorization = decision.get("authorization") or ((contract.get("construction") or {}).get("conversational_authorization"))
        social_invoked = bool(social)
        execute_expected = expect in {"execute_npc", "execute_after_reload"}
        handoff = social_invoked == execute_expected or (expect == "inspect")
        if expect == "preserve_both_no_flatten":
            handoff = not social_invoked
        response_ok = True
        if expect in {"clarify_no_mutation", "gm_no_social", "revise_no_execution", "cannot_undo", "ask_what_to_change", "withdraw_no_execution"}:
            response_ok = "says," not in lowered
        if execute_expected:
            response_ok = "cannot be identified" not in lowered and "which person do you mean" not in lowered
        return {
            "behavior_pass": bool(behavior),
            "state_pass": (not mutated) if expect not in {"execute_npc", "execute_after_reload"} else bool(mutated or social_invoked),
            "label_pass": label_pass,
            "handoff_pass": bool(handoff),
            "response_pass": bool(response_ok and behavior),
            "authorization_present": isinstance(authorization, dict),
            "authorization": authorization,
            "actual_recipient": (communication or {}).get("recipient"),
            "actual_purpose": (communication or {}).get("purpose"),
            "social_npc": social.get("npc_id"),
            "kind": resolution.get("kind"),
            "response": text,
        }

    rows = {"conversation": [], "holdouts": [], "performance": []}

    def write():
        payload = scrub({"rows": rows, "provider": snapshot()})
        (OUT / "live_qualification.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    (ROOT / "development" / "tmp").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pr_ef_r4_", dir=ROOT / "development" / "tmp") as temp, pytest.MonkeyPatch.context() as mp:
        temp_path = Path(temp)

        def reset(two_npcs=False):
            seed_scene(temp_path, mp)
            os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
            os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"
            if two_npcs:
                _add_bren(None, role="guard")

        client = TestClient(app)
        reset(two_npcs=True)
        for number, (text, expect) in enumerate(conversation, 1):
            if number == 6:
                storage.save_session(copy.deepcopy(storage.load_session()))
            start = time.perf_counter()
            cursor = len(snapshot().get("records") or [])
            before = compact(storage.load_session(), storage.load_world())
            response = client.post("/api/chat?ui_mode=player", json={"text": text, "ui_mode": "player"})
            data = response.json()
            after_session = storage.load_session()
            after = compact(after_session, storage.load_world())
            answer = (data.get("gm_output") or {}).get("player_facing_text") or ""
            ok, mutated = score_behavior(expect, data, before, after, answer)
            records = turn_records(cursor)
            resolution = data.get("resolution") or {}
            metadata = resolution.get("metadata") or {}
            decision = metadata.get("conversational_decision") or {}
            contract = (metadata.get("resolution_contract") or {}).get("construction") or {}
            row = {
                "turn": number,
                "player": text,
                "expected": expect,
                "behavior_pass": ok and response.status_code == 200,
                "critical_unauthorized_mutation": expect in {"gm_no_mutation", "clarify_no_mutation", "cannot_undo", "no_move"} and mutated,
                "http_status": response.status_code,
                "response": answer,
                "kind": resolution.get("kind"),
                "social": resolution.get("social"),
                "raw_interpretation": (metadata.get("live_chat_interpretation") or {}).get("raw_interpretation"),
                "interpretation_record": (metadata.get("live_chat_interpretation") or {}).get("record"),
                "authorization": decision.get("authorization") or contract.get("conversational_authorization"),
                "decision_reason": decision.get("reason"),
                "decision_owner": decision.get("communication_owner"),
                "resolver_invoked": metadata.get("resolver_invoked"),
                "state_before": before,
                "state_after": after,
                "pending_after": (after_session.get("conversational_context") or {}).get("pending_intention"),
                "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
                "calls": summarize_calls(records),
            }
            rows["conversation"].append(scrub(row))
            write()
            print(json.dumps({"phase": "conversation", "turn": number, "pass": row["behavior_pass"], "kind": row["kind"], "calls": row["calls"]["provider_calls"]}), flush=True)

        performance_cases = [
            ("A_established_dialogue", "I ask Sergeant Mara about the north road.", False),
            ("B_unavailable_answer", "I ask Sergeant Mara who forged the lantern.", False),
            ("C_gm_question", "Could you describe our surroundings?", False),
            ("D_consequential_inspect", "I inspect the courtyard lantern.", False),
            ("E_ambiguous", "I ask one of them what happened.", True),
        ]
        for name, text, two in performance_cases:
            reset(two_npcs=two)
            if name.startswith("A_"):
                client.post("/api/chat?ui_mode=player", json={"text": "I ask Sergeant Mara where the street leads.", "ui_mode": "player"})
            start = time.perf_counter()
            cursor = len(snapshot().get("records") or [])
            response = client.post("/api/chat?ui_mode=player", json={"text": text, "ui_mode": "player"})
            data = response.json()
            records = turn_records(cursor)
            rows["performance"].append(scrub({
                "case": name,
                "player": text,
                "response": (data.get("gm_output") or {}).get("player_facing_text"),
                "kind": (data.get("resolution") or {}).get("kind"),
                "social": (data.get("resolution") or {}).get("social"),
                "elapsed_ms": round((time.perf_counter() - start) * 1000, 3),
                "calls": summarize_calls(records),
            }))
            write()
            print(json.dumps({"phase": "performance", "case": name, "calls": rows["performance"][-1]["calls"]}), flush=True)

        for case in HOLDOUTS["cases"]:
            reset(two_npcs=False)
            _prepare(case)
            if case.get("setup") == "save_load_ambiguous":
                storage.save_session(copy.deepcopy(storage.load_session()))
            start = time.perf_counter()
            cursor = len(snapshot().get("records") or [])
            before = _integrity(storage.load_session(), storage.load_world())
            response = client.post("/api/chat?ui_mode=player", json={"text": case["player"], "ui_mode": "player"})
            data = response.json()
            after = _integrity(storage.load_session(), storage.load_world())
            scored = score_holdout(case, data, before, after)
            records = turn_records(cursor)
            row = {"id": case["id"], "player": case["player"], "expect": case["expect"], "elapsed_ms": round((time.perf_counter() - start) * 1000, 3), "calls": summarize_calls(records), **scored}
            rows["holdouts"].append(scrub(row))
            write()
            print(json.dumps({"phase": "holdout", "id": case["id"], "behavior": row["behavior_pass"], "label": row["label_pass"]}), flush=True)

    write()
    print(json.dumps({"status": "complete", "provider": {k: snapshot().get(k) for k in ("requests", "input_tokens", "output_tokens", "total_tokens", "stopped", "stop_reason")}}), flush=True)


if __name__ == "__main__":
    main()
