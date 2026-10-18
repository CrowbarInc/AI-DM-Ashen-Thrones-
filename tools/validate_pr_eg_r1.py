"""PR-EG-R1 fresh-provider qualification through production /api/chat.

Two disposable campaigns. Expectations are read from the frozen fixture and
are not rewritten after the provider responds.
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
OUT = ROOT / "artifacts" / "pr_eg_r1"
sys.path.insert(0, str(ROOT))
_SECRET = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")
EXPECTATIONS = json.loads(
    (ROOT / "tests" / "fixtures" / "pr_eg_r1_live_expectations.json").read_text(encoding="utf-8")
)

PRIMARY = [
    "Could you describe the courtyard?",
    "I ask Sergeant Mara what the street beyond the gate is called.",
    "What did you mean by that?",
    "Say that again in plainer words.",
    "Do you prefer the morning or the evening?",
    "Why that one, then?",
    "What is the street called?",
    "Who forged the lantern?",
    "I meant the road, not how you feel.",
    "Promise me a reward if I carry a message for you.",
    "Swear you'll pay me ten silver if I do it.",
    "I inspect the courtyard lantern.",
    "I walk through the courtyard gate.",
    "Earlier you could not tell me who forged the lantern. Is that still where you stand?",
    "GM, what did she say the street was called?",
]

SECOND = [
    "What can I see from here?",
    "Sergeant Mara, is there a name for the road past the barred gate?",
    "Sorry, what was that name?",
    "Do you like the quiet of morning better than evening?",
    "You'd pick the same if I asked again?",
    "Has the lantern's maker ever been named?",
    "I was asking about the road's name, not the lantern.",
    "If I take a message to the gate for you, will you promise me something for it?",
    "I look closely at the lantern.",
    "I head through the courtyard gate.",
    "Back in the courtyard you named a road. What was it?",
    "GM, repeat what Mara said about that road.",
]


def scrub(value):
    text = json.dumps(value, ensure_ascii=False, default=str)
    return json.loads(_SECRET.sub("[redacted]", text))


def compact(session, world):
    return {
        "turn_counter": (session or {}).get("turn_counter"),
        "scene": (session or {}).get("active_scene_id") or ((session or {}).get("scene_state") or {}).get("active_scene_id"),
        "clocks": copy.deepcopy((session or {}).get("clocks") or (world or {}).get("clocks")),
        "factions": [
            {key: row.get(key) for key in ("id", "attitude", "influence")}
            for row in ((world or {}).get("factions") or [])
            if isinstance(row, dict)
        ],
        "topics": [
            {"id": npc.get("id"), "topics": [t.get("id") if isinstance(t, dict) else t for t in (npc.get("topics") or [])]}
            for npc in ((world or {}).get("npcs") or [])
            if isinstance(npc, dict)
        ],
    }


def calls_since(snapshot, start):
    rows = [row for row in (snapshot().get("records") or [])[start:] if row.get("sent")]

    def count(purpose):
        return sum(1 for row in rows if row.get("purpose") == purpose)

    return {
        "provider_calls": len(rows),
        "interpretation_calls": count("interpretation"),
        "narration_calls": sum(1 for row in rows if row.get("purpose") not in {"interpretation", "retry_escalation", "expression"}),
        "expression_calls": count("expression"),
        "retry_calls": count("retry_escalation"),
        "input_tokens": sum(int(row.get("input_tokens") or 0) for row in rows),
        "output_tokens": sum(int(row.get("output_tokens") or 0) for row in rows),
        "purposes": [row.get("purpose") for row in rows],
    }


def score_turn(number, text, usage, checks):
    spec = checks.get(str(number)) or {}
    lowered = text.lower()
    failures = []
    for bit in spec.get("contain") or []:
        if bit.lower() not in lowered:
            failures.append(f"missing:{bit}")
    if spec.get("contain_any") and not any(bit.lower() in lowered for bit in spec["contain_any"]):
        failures.append("missing_any:" + "|".join(spec["contain_any"]))
    for bit in spec.get("forbid") or []:
        if bit.lower() in lowered:
            failures.append(f"forbidden:{bit}")
    if "max_retries" in spec and usage["retry_calls"] > spec["max_retries"]:
        failures.append("retries")
    if "max_narration" in spec and usage["narration_calls"] > spec["max_narration"]:
        failures.append("narration")
    return failures


def run_conversation(client, lines, checks, storage, snapshot):
    rows = []
    for number, text in enumerate(lines, 1):
        cursor = len(snapshot().get("records") or [])
        before = compact(storage.load_session(), storage.load_world())
        started = time.perf_counter()
        response = client.post("/api/chat?ui_mode=player", json={"text": text, "ui_mode": "player"})
        data = response.json()
        answer = ((data.get("gm_output") or {}).get("player_facing_text") or "")
        resolution = data.get("resolution") or {}
        social = resolution.get("social") or {}
        metadata = resolution.get("metadata") or {}
        decision = metadata.get("conversational_decision") or {}
        contract = (metadata.get("resolution_contract") or {}).get("construction") or {}
        after = compact(storage.load_session(), storage.load_world())
        usage = calls_since(snapshot, cursor)
        lowered = answer.lower()
        global_hits = [bit for bit in EXPECTATIONS["global_forbidden"] if bit in lowered]
        row = {
            "turn": number,
            "player": text,
            "http_status": response.status_code,
            "response": answer,
            "kind": resolution.get("kind"),
            "reason": decision.get("reason"),
            "authorization": decision.get("authorization") or contract.get("conversational_authorization"),
            "dialogue_authority": social.get("dialogue_authority"),
            "active_interlocutor": ((storage.load_session().get("interaction_context") or {}).get("active_interaction_target_id")),
            "state_changed_keys": [key for key in ("turn_counter", "scene", "clocks", "factions", "topics") if before.get(key) != after.get(key)],
            "topics_unchanged": before.get("topics") == after.get("topics"),
            "factions_unchanged": before.get("factions") == after.get("factions"),
            "calls": usage,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "frozen_failures": score_turn(number, answer, usage, checks) + [f"global:{bit}" for bit in global_hits],
        }
        rows.append(scrub(row))
        print(json.dumps({
            "turn": number,
            "calls": usage["provider_calls"],
            "in": usage["input_tokens"],
            "retry": usage["retry_calls"],
            "failures": row["frozen_failures"],
            "text": answer[:180],
        }), flush=True)
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    usage_path = OUT / "live.usage.jsonl"
    if usage_path.exists():
        usage_path.unlink()
    os.environ.update(
        ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT="1",
        ASHEN_DISABLE_PROVIDER_CALLS="0",
        ASHEN_DISABLE_LIVE_INTERPRETATION="0",
        ASHEN_PROVIDER_REQUEST_LIMIT="120",
        ASHEN_PROVIDER_INPUT_TOKEN_LIMIT="1000000",
        ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT="60000",
        ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT="1060000",
        ASHEN_PROVIDER_TIMEOUT_SECONDS="45",
        ASHEN_NARRATION_MAX_OUTPUT_TOKENS="700",
        ASHEN_PROVIDER_USAGE_PATH=str(usage_path),
    )
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    if not os.environ.get("OPENAI_API_KEY"):
        print(json.dumps({"status": "UNVERIFIED", "reason": "key_missing"}), flush=True)
        return

    import pytest
    from fastapi.testclient import TestClient

    from game import storage
    from game.api import app
    from game.provider_budget import snapshot
    from tests.test_pr_ef_gm_authority import seed_scene

    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"
    (ROOT / "development" / "tmp").mkdir(parents=True, exist_ok=True)
    payload = {"model_configured": "gpt-4.1-mini"}
    with tempfile.TemporaryDirectory(prefix="pr_eg_r1_a_", dir=ROOT / "development" / "tmp") as temp, pytest.MonkeyPatch.context() as mp:
        seed_scene(Path(temp), mp)
        os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
        client = TestClient(app)
        payload["primary"] = run_conversation(client, PRIMARY, EXPECTATIONS["primary"]["checks"], storage, snapshot)
    with tempfile.TemporaryDirectory(prefix="pr_eg_r1_b_", dir=ROOT / "development" / "tmp") as temp, pytest.MonkeyPatch.context() as mp:
        seed_scene(Path(temp), mp)
        os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
        client = TestClient(app)
        payload["second"] = run_conversation(client, SECOND, EXPECTATIONS["second"]["checks"], storage, snapshot)
    primary_fail = sum(len(row["frozen_failures"]) for row in payload["primary"])
    second_fail = sum(len(row["frozen_failures"]) for row in payload["second"])
    payload["primary_frozen_failures"] = primary_fail
    payload["second_frozen_failures"] = second_fail
    payload["primary_turns"] = len(payload["primary"])
    payload["second_turns"] = len(payload["second"])
    (OUT / "live_qualification.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "recorded",
        "primary_failures": primary_fail,
        "second_failures": second_fail,
    }), flush=True)


if __name__ == "__main__":
    main()
