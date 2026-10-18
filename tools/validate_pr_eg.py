"""PR-EG fresh-provider dialogue qualification through production /api/chat.

Disposable campaign only. Does not print secrets.
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
OUT = ROOT / "artifacts" / "pr_eg"
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
        ASHEN_PROVIDER_REQUEST_LIMIT="80",
        ASHEN_PROVIDER_INPUT_TOKEN_LIMIT="800000",
        ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT="40000",
        ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT="840000",
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
    from game.dialogue_authority import response_class
    from game.provider_budget import snapshot
    from tests.test_pr_ef_gm_authority import seed_scene

    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"

    conversation = [
        "Could you describe the courtyard?",
        "I ask Sergeant Mara what the street beyond the gate is called.",
        "What did you mean by that?",
        "Has anyone been keeping an eye on it after dark?",
        "I ask Mara who forged the lantern.",
        "What troubles you, standing out here?",
        "Do you prefer the morning or the evening?",
        "I meant the road, not how you feel.",
        "What is the password for the side gate?",
        "Promise me a reward if I carry a message for you.",
        "I walk through the courtyard gate.",
        "Earlier you could not tell me who watches the north road. Is that still where you stand?",
    ]

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

    def calls_since(start):
        rows = [row for row in (snapshot().get("records") or [])[start:] if row.get("sent")]
        def count(purpose):
            return sum(1 for row in rows if row.get("purpose") == purpose)
        return {
            "provider_calls": len(rows),
            "interpretation_calls": count("interpretation"),
            "narration_calls": sum(1 for row in rows if row.get("purpose") not in {"interpretation", "retry_escalation"}),
            "retry_calls": count("retry_escalation"),
            "input_tokens": sum(int(row.get("input_tokens") or 0) for row in rows),
            "output_tokens": sum(int(row.get("output_tokens") or 0) for row in rows),
            "purposes": [row.get("purpose") for row in rows],
        }

    def dimensions(text, social, usage):
        authority = (social or {}).get("dialogue_authority") or {}
        lowered = text.lower()
        kind = response_class(text)
        narration_cap = 0 if authority.get("narration_determined") else 1
        return {
            "relevance": kind != "answer" or authority.get("requested_information") in {None, "general", "personal_state", "opinion"} or authority.get("answer_relation") in {"sufficient", "partial"},
            "groundedness": kind != "consequential" and "password is" not in lowered and "i'll pay" not in lowered and "usually a patrol" not in lowered,
            "naturalness": "settled here" not in lowered and "speech authority" not in lowered,
            "uncertainty_quality": authority.get("knowledge_posture"),
            "improvisation": authority.get("improvisation_permitted"),
            "efficiency": usage["retry_calls"] == 0 and usage["narration_calls"] <= narration_cap and usage["interpretation_calls"] <= 1,
            "class": kind,
        }

    rows = []
    (ROOT / "development" / "tmp").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pr_eg_", dir=ROOT / "development" / "tmp") as temp, pytest.MonkeyPatch.context() as mp:
        seed_scene(Path(temp), mp)
        os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
        client = TestClient(app)
        for number, text in enumerate(conversation, 1):
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
            usage = calls_since(cursor)
            row = {
                "turn": number,
                "player": text,
                "http_status": response.status_code,
                "response": answer,
                "kind": resolution.get("kind"),
                "authorization": decision.get("authorization") or contract.get("conversational_authorization"),
                "dialogue_authority": social.get("dialogue_authority"),
                "reply_plan_kind": social.get("reply_plan_kind"),
                "npc_speech_authority": social.get("npc_speech_authority"),
                "topic_revealed": (social.get("topic_revealed") or {}).get("id") if isinstance(social.get("topic_revealed"), dict) else None,
                "dimensions": dimensions(answer, social, usage),
                "state_changed_keys": [key for key in ("turn_counter", "scene", "clocks", "factions", "topics") if before.get(key) != after.get(key)],
                "topics_unchanged": before.get("topics") == after.get("topics"),
                "calls": usage,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            }
            rows.append(scrub(row))
            (OUT / "live_qualification.json").write_text(json.dumps({"conversation": rows}, indent=2), encoding="utf-8")
            print(json.dumps({
                "turn": number,
                "class": row["dimensions"]["class"],
                "calls": usage["provider_calls"],
                "narration": usage["narration_calls"],
                "retry": usage["retry_calls"],
                "input_tokens": usage["input_tokens"],
                "natural": row["dimensions"]["naturalness"],
            }), flush=True)
    print(json.dumps({"status": "recorded", "turns": len(rows)}), flush=True)


if __name__ == "__main__":
    main()
