"""Fresh-provider qualification for expression semantics and relevance.

Disposable campaigns only. Interpretation and expression use the configured
provider. Narration is not required. No recorded replies.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "artifacts" / "pr_eg_r3_r1"

PRIMARY = [
    ("I ask Sergeant Mara, do you prefer the morning or the evening?", "preference", ["evening"], ["guard"]),
    ("Why do you prefer the evening?", "characterization", ["evening"], ["guard", "unattended", "silver", "captain"]),
    ("I ask Sergeant Mara what the street beyond the gate is called.", "fact", ["north road"], ["capital"]),
    ("Say that another way.", "paraphrase", ["north road"], ["capital", "north street"]),
    ("Say that in simpler words.", "paraphrase", ["north road", "gate"], ["capital"]),
    ("What did you mean by the north road?", "explanation", ["north road"], ["which earlier", "capital"]),
    ("I ask Sergeant Mara who made the lantern.", "uncertainty", ["know"], ["smith", "capital"]),
    ("Promise me a reward if I help you.", "refusal", ["promise"], ["silver", "i will pay"]),
    ("I ask Sergeant Mara whether guards watch the north gate at night.", "authorized", ["guard", "night"], ["unattended"]),
    ("Is the north gate ever left unattended?", "partial", ["night", "couldn't"], ["never", "password"]),
    ("GM, what exactly did Mara say about the road?", "recall", ["north road"], ["capital"]),
    ("GM, what did Mara say about the gate?", "ambiguity", ["which"], ["capital", "password"]),
    ("GM, what did Mara say about the night?", "clarify", ["night"], ["capital"]),
    ("What do you enjoy about the evening?", "characterization", ["evening"], ["guard", "silver"]),
    ("Do you still prefer the evening?", "preference", ["evening"], ["guard"]),
]
SECONDARY = [
    ("I ask Keeper Nara whether guards watch the harbor gate at night.", "authorized", ["guard", "harbor"], ["unattended"]),
    ("Is the harbor gate ever left unguarded?", "partial", ["harbor", "couldn't"], ["never", "password"]),
    ("I ask Keeper Nara what the bell beside the ferry is called.", "fact", ["harbor bell"], ["smuggler"]),
    ("Say that another way.", "paraphrase", ["harbor", "bell"], ["smuggler", "password"]),
    ("Do you prefer the morning or the evening?", "preference", ["evening"], ["guard"]),
    ("What do you enjoy about the evening?", "characterization", ["evening"], ["guard", "silver", "captain"]),
    ("I ask Keeper Nara who owns the ferry bell.", "uncertainty", ["know"], ["wren", "smith"]),
    ("Promise me a reward if I mend the net.", "refusal", ["promise"], ["silver", "i will pay"]),
    ("GM, what exactly did Nara say the harbor bell is called?", "recall", ["harbor bell"], ["smuggler"]),
    ("Why do you prefer the evening?", "characterization", ["evening"], ["guard", "silver"]),
    ("GM, what did Nara say about the harbor?", "ambiguity", ["which"], ["smuggler"]),
    ("GM, what did Nara say about the harbor bell?", "clarify", ["harbor bell"], ["smuggler"]),
]


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def diff(before, after, path=""):
    if isinstance(before, dict) and isinstance(after, dict):
        rows = []
        for key in sorted(set(before) | set(after)):
            rows.extend(diff(before.get(key), after.get(key), path + "/" + str(key)))
        return rows
    if isinstance(before, list) and isinstance(after, list):
        if before == after:
            return []
        return [dict(path=path, before=before, after=after)]
    return [] if before == after else [dict(path=path, before=before, after=after)]


def _unsafe(text, absent):
    low = text.lower()
    hits = [bit for bit in absent if bit and bit.lower() in low]
    if re.search(r"\bnever (?:left )?(?:unattended|unguarded|unwatched)\b", low):
        hits.append("absence_asserted")
    if re.search(r"\b(?:the gate|it) is (?:left )?unattended\b", low):
        hits.append("unattended_asserted")
    if re.search(r"\bi will pay\b|\bi'll pay\b|\bi promise you a reward\b", low):
        hits.append("unauthorized_commitment")
    return hits


def score_row(kind, text, audit, failures):
    if failures:
        return 0
    adopted = isinstance(audit, dict) and audit.get("decision") == "adopted"
    expressive = kind in {"paraphrase", "explanation", "characterization", "uncertainty", "refusal"}
    if expressive and adopted:
        return 3
    if kind == "partial":
        return 3
    if kind in {"ambiguity", "clarify", "recall"}:
        return 3
    if expressive:
        return 1
    return 2


def failures_for(kind, text, contains, absent, audit):
    low = text.lower()
    found = []
    for bit in contains:
        if bit.lower() not in low:
            if bit == "know" and any(token in low for token in ["couldn't", "don't know", "do not know", "not sure", "no idea"]):
                continue
            if bit == "promise" and any(token in low for token in ["can't", "cannot", "won't", "couldn"]):
                continue
            if bit == "which" and "do you mean" in low:
                continue
            found.append("missing:" + bit)
    found.extend(_unsafe(text, absent))
    if kind == "partial":
        if not re.search(r"\b(?:could(?:n't| not)|cannot|can't|not sure)\b", low):
            found.append("partial_presented_as_complete")
        if re.search(r"\b(?:^yes\b|^no\b)\b", low):
            found.append("unsupported_yes_no")
    if kind in {"paraphrase", "explanation"} and isinstance(audit, dict) and audit.get("decision") == "adopted":
        proposition = " ".join((audit.get("contract") or {}).get("authorized_propositions") or []).lower()
        if proposition and proposition in low:
            found.append("verbatim_adopted")
    if any(bit in low for bit in ["carry out that request", "another route", "who are you asking", "which person are you"]):
        found.append("unrelated_fallback")
    return found


def main():
    OUT.mkdir(exist_ok=True)
    plan = dict(primary=PRIMARY, secondary=SECONDARY)
    if sys.argv[-1] == "freeze":
        write("live_plan.json", plan)
        write("live_freeze.json", dict(sha256=hashlib.sha256((OUT / "live_plan.json").read_bytes()).hexdigest(), stage="before fresh provider qualification"))
        return
    frozen = json.loads((OUT / "live_plan.json").read_text(encoding="utf-8"))
    assert frozen == json.loads(json.dumps(plan))
    os.environ.update(
        ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT="1",
        ASHEN_DISABLE_PROVIDER_CALLS="0",
        ASHEN_DISABLE_LIVE_INTERPRETATION="0",
        ASHEN_DISABLE_EXPRESSION_GENERATION="0",
        ASHEN_PROVIDER_REQUEST_LIMIT="90",
        ASHEN_PROVIDER_INPUT_TOKEN_LIMIT="1000000",
        ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT="60000",
        ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT="1060000",
        ASHEN_PROVIDER_TIMEOUT_SECONDS="45",
        ASHEN_PROVIDER_USAGE_PATH=str(OUT / "live_usage.jsonl"),
    )
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    if not os.environ.get("OPENAI_API_KEY"):
        write("live_status.json", dict(status="UNVERIFIED", reason="key_missing"))
        return
    import pytest
    from fastapi.testclient import TestClient

    from game import storage
    from game.api import app
    from game.provider_budget import snapshot
    from tests.test_pr_ef_gm_authority import seed_scene
    from tools.validate_pr_eg_r1 import calls_since

    all_rows = {}
    for label, turns in (("primary", PRIMARY), ("secondary", SECONDARY)):
        with pytest.MonkeyPatch.context() as mp:
            data_dir = OUT / "disposable_state" / ("live_" + label)
            seed_scene(data_dir, mp)
            if label == "secondary":
                for path in data_dir.rglob("*.json"):
                    path.write_text(
                        path.read_text(encoding="utf-8").replace("sergeant_mara", "keeper_nara").replace("Sergeant Mara", "Keeper Nara"),
                        encoding="utf-8",
                    )
            world = storage.load_world()
            target = "sergeant_mara" if label == "primary" else "keeper_nara"
            for npc in world["npcs"]:
                if npc["id"] == target:
                    if label == "primary":
                        npc.setdefault("topics", []).append(dict(id="night_watch", text="Guards watch the north gate throughout the night."))
                    else:
                        npc["topics"] = [
                            dict(id="bell", text="The bell beside the ferry is called the harbor bell."),
                            dict(id="harbor_watch", text="Guards watch the harbor gate throughout the night."),
                        ]
            storage.save_world(world)
            mp.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "0")
            mp.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "0")
            mp.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "0")
            rows = []
            all_rows[label] = rows
            client = TestClient(app)
            for number, (player, kind, contains, absent) in enumerate(turns, 1):
                world_before = copy.deepcopy(storage.load_world())
                session_before = copy.deepcopy(storage.load_session())
                start = len(snapshot()["records"])
                started = time.perf_counter()
                response = client.post("/api/chat?ui_mode=player", json=dict(text=player, ui_mode="player"))
                elapsed = (time.perf_counter() - started) * 1000
                try:
                    result = response.json()
                except Exception:
                    result = {"raw": response.text[:500]}
                world_after = copy.deepcopy(storage.load_world())
                session_after = copy.deepcopy(storage.load_session())
                gm = result.get("gm_output") or {}
                text = str(gm.get("player_facing_text") or "")
                metadata = gm.get("metadata") or {}
                acceptance = metadata.get("accepted_response") or {}
                audit = metadata.get("expression_generation") or None
                history = (session_after.get("conversational_context") or {}).get("delivered_exchanges") or []
                failed = failures_for(kind, text, contains, absent, audit)
                if response.status_code != 200:
                    failed.append("http_" + str(response.status_code))
                if acceptance and text != acceptance.get("text"):
                    failed.append("adoption_text_mismatch")
                if history and history[-1].get("delivered_text") != text:
                    failed.append("delivered_history_mismatch")
                if audit and audit.get("decision") == "rejected" and audit.get("candidate") and audit["candidate"].lower() in text.lower():
                    failed.append("rejected_candidate_delivered")
                usage = calls_since(snapshot, start)
                if kind in {"recall", "ambiguity", "clarify"} and usage.get("expression_calls"):
                    failed.append("recall_used_expression")
                if usage.get("narration_calls"):
                    failed.append("narration_call")
                if usage.get("retry_calls"):
                    failed.append("retry_call")
                world_diff = diff(world_before, world_after)
                nonpassive = [
                    row for row in world_diff
                    if not str(row["path"]).startswith(("/factions", "/event_log"))
                    and not (str(row["path"]).startswith("/world_state/flags/faction_") and str(row["path"]).endswith("_agenda_advanced"))
                ]
                if nonpassive:
                    failed.append("nonpassive_world_change")
                row = dict(
                    turn=number,
                    player=player,
                    kind=kind,
                    http_status=response.status_code,
                    text=text,
                    calls=usage,
                    elapsed_ms=round(elapsed, 1),
                    adoption=acceptance,
                    expression=audit,
                    history=[
                        dict(
                            speaker_id=item.get("speaker_id"),
                            delivered_text=item.get("delivered_text"),
                            proposition_id=item.get("proposition_id"),
                            authorized_proposition=item.get("authorized_proposition"),
                            answer_sufficiency=item.get("answer_sufficiency"),
                            authorization_source=item.get("authorization_source"),
                        )
                        for item in history
                    ],
                    commitment_diff=diff(
                        (session_before.get("conversational_context") or {}).get("dialogue_commitments"),
                        (session_after.get("conversational_context") or {}).get("dialogue_commitments"),
                    ),
                    world_diff=world_diff,
                    world_nonpassive_diff=nonpassive,
                    failures=failed,
                    score=score_row(kind, text, audit, failed),
                    save_load=None,
                    resolution_kind=(result.get("resolution") or {}).get("kind"),
                )
                if number in {4, 8, len(turns)}:
                    storage.save_session(copy.deepcopy(session_after))
                    loaded = storage.load_session()
                    row["save_load"] = dict(context_equal=loaded.get("conversational_context") == session_after.get("conversational_context"))
                    if not row["save_load"]["context_equal"]:
                        failed.append("save_load_mismatch")
                        row["failures"] = failed
                        row["score"] = score_row(kind, text, audit, failed)
                rows.append(row)
                write("live_qualification.json", all_rows)
                print(json.dumps(dict(conversation=label, turn=number, kind=kind, calls=usage.get("provider_calls"), expression=usage.get("expression_calls"), score=row["score"], failures=failed, text=text), ensure_ascii=False), flush=True)
    summary = {}
    adopted_characterization = []
    for label, rows in all_rows.items():
        adopted = [row["turn"] for row in rows if isinstance(row.get("expression"), dict) and row["expression"].get("decision") == "adopted"]
        for row in rows:
            audit = row.get("expression") or {}
            if row["kind"] == "characterization" and audit.get("decision") == "adopted" and audit.get("candidate") and audit["candidate"] in row["text"]:
                adopted_characterization.append(dict(conversation=label, turn=row["turn"], text=row["text"]))
        summary[label] = dict(
            turns=len(rows),
            adopted_turns=adopted,
            scores=[row["score"] for row in rows],
            failures={str(row["turn"]): row["failures"] for row in rows if row["failures"]},
        )
    write("live_status.json", dict(status="executed", summary=summary, adopted_characterization=adopted_characterization))


if __name__ == "__main__":
    main()
