"""Deterministic PR-PLAY-79D-F2 holdout runner. No live provider."""
from __future__ import annotations

import json

from game.dialogue_authority import remember_dialogue_commitment
from game.publication_contract import note_completed_publication, record_completed_publication, summarize_provider_rows
from tests.test_pr_play_79df2_publication import (
    ACCEPTED,
    FALLBACK,
    _rejected_gm,
    _session,
)


def _base():
    return _session()


def run_case(row, monkeypatch, tmp_path):
    kind = row["kind"]
    expect = row["expect"]
    if kind == "accept":
        spoken = 'Gate Guard says, "I do not know anything beyond the warning about a missing patrol."'
        session = _base()
        record = note_completed_publication(session, text=spoken, gm={"metadata": {"expression_generation": {
            "decision": "adopted", "fallback_used": False,
            "candidate": "I do not know anything beyond the warning about a missing patrol.",
            "delivered_generated": True,
        }}})
        return _ok(record, expect, session)
    if kind == "fallback":
        session = _base()
        record = note_completed_publication(session, text=FALLBACK, gm=_rejected_gm())
        return _ok(record, expect, session)
    if kind == "roundtrip":
        session = _base()
        note_completed_publication(session, text=FALLBACK, gm=_rejected_gm())
        restored = json.loads(json.dumps(session))
        return {
            "pass": restored["last_publication"]["visible"] == FALLBACK and restored["last_publication"]["dialogue_accepted"] is False,
            "visible_survives": restored["last_publication"]["visible"] == FALLBACK,
            "accepted_survives": restored["last_publication"]["dialogue_accepted"],
        }
    if kind == "commitment":
        session = _base()
        flags = json.dumps(session["world_state"])
        entry = remember_dialogue_commitment(session, social={"npc_id": "gate_guard", "dialogue_authority": {
            "npc_id": "gate_guard", "knowledge_posture": "unknown", "subject": "board", "authorized_proposition": "",
        }}, player_text="What does it say?", line=FALLBACK, turn=4)
        return {"pass": entry["canonical"] is False and json.dumps(session["world_state"]) == flags,
                "canonical": entry["canonical"], "flags_unchanged": json.dumps(session["world_state"]) == flags}
    if kind == "narration":
        from tests.pr_play_79df_executor import physical
        acted = physical(monkeypatch, row["transport"], narrate=True)
        return {"pass": acted["calls"] == expect["calls"] and acted["live"] is expect["live"],
                "calls": acted["calls"], "live": acted["live"]}
    if kind == "narration_reject":
        from tests.pr_play_79df_executor import physical
        acted = physical(monkeypatch, row["transport"], narrate=True)
        text = acted["published"].casefold()
        excluded = all(piece not in text for piece in expect.get("excludes") or [])
        return {"pass": acted["calls"] == expect.get("calls", 1) and acted["live"] is expect["live"] and excluded,
                "calls": acted["calls"], "live": acted["live"], "published": acted["published"]}
    if kind == "recall":
        from tests.test_pr_play_79d_closeout import exercise_recall
        recalled = list(exercise_recall("chart", "The chart records four moons.", row["condition"]))
        return {"pass": recalled == expect["recalled"], "recalled": recalled}
    if kind == "event":
        session = _base()
        note_completed_publication(session, text=FALLBACK, gm=_rejected_gm())
        event = record_completed_publication(
            {"gm_output": {"player_facing_text": FALLBACK}},
            source_handler="api_chat",
            publication_context=session["last_publication"],
            provider_rows=[{"sent": True, "attempt_id": "held"}],
        )
        return {"pass": event["validation_outcome"] == "engine_or_grounded_fallback" and not event["accepted_expression_references"],
                "validation": event["validation_outcome"], "accepted_refs": len(event["accepted_expression_references"])}
    if kind == "isolation":
        first = _base()
        second = _session(visible='Serjeant says, "Hold."', campaign="beta", turn=1)
        note_completed_publication(first, text=FALLBACK, gm=_rejected_gm())
        beta_visible = second["last_publication"]["visible"]
        return {"pass": beta_visible == 'Serjeant says, "Hold."' and first["last_publication"]["campaign_run_id"] == "alpha",
                "beta_untouched": second["last_publication"]["campaign_run_id"] == "beta",
                "beta_visible": beta_visible}
    if kind == "keep":
        session = _session(visible='Gate Guard says, "Evening."', accepted=True)
        note_completed_publication(session, text='Gate Guard says, "Evening."')
        record = session["last_publication"]
        return {"pass": record["owner"] == "integrated_play.commit_integrated" and record["dialogue_accepted"] is True,
                "owner": record["owner"], "dialogue_accepted": record["dialogue_accepted"]}
    if kind == "reject_same":
        session = _session(visible=FALLBACK, accepted=True)
        record = note_completed_publication(session, text=FALLBACK, gm=_rejected_gm())
        return {"pass": record["dialogue_accepted"] is False and record["fallback"] is True,
                "dialogue_accepted": record["dialogue_accepted"], "fallback": record["fallback"]}
    if kind == "empty":
        session = _base()
        before = session["last_publication"]["visible"]
        note_completed_publication(session, text="")
        return {"pass": session["last_publication"]["visible"] == before, "unchanged": session["last_publication"]["visible"] == before}
    if kind == "speech_narration":
        session = _base()
        session["last_narration"] = {"adopted": True, "candidate": "You step back."}
        record = note_completed_publication(session, text=FALLBACK, gm=_rejected_gm())
        return {"pass": record["narration_accepted"] is False and record["dialogue_published"] is True,
                "narration_accepted": record["narration_accepted"], "dialogue_published": record["dialogue_published"]}
    if kind == "physical_record":
        line = "You take a step backward away from the Notice board."
        session = _base()
        session["last_narration"] = {"adopted": True, "candidate": line}
        record = note_completed_publication(session, text=line)
        return {"pass": record["narration_published"] is True and record["dialogue_published"] is False,
                "narration_published": record["narration_published"], "dialogue_published": record["dialogue_published"]}
    if kind == "renderer":
        from tests.pr_play_79df_executor import renderer
        result = renderer(monkeypatch)
        return {"pass": result["unchanged"] is True and result["same_text"] is True, "unchanged": result["unchanged"]}
    if kind == "uncertainty":
        session = _base()
        line = 'Gate Guard says, "I am not certain."'
        entry = remember_dialogue_commitment(session, social={"npc_id": "gate_guard", "dialogue_authority": {
            "npc_id": "gate_guard", "knowledge_posture": "unknown", "subject": "time", "authorized_proposition": "",
        }}, player_text="When exactly?", line=line, turn=3)
        return {"pass": entry["canonical"] is False and entry["kind"] == "admitted_uncertainty",
                "canonical": entry["canonical"], "kind": entry["kind"]}
    if kind == "established":
        session = _base()
        entry = remember_dialogue_commitment(session, social={"npc_id": "gate_guard", "dialogue_authority": {
            "knowledge_posture": "established", "npc_id": "gate_guard", "subject": "board",
        }}, player_text="Again?", line=FALLBACK, turn=3)
        return {"pass": entry is None, "stored": entry is not None}
    if kind == "accounting":
        summary = summarize_provider_rows([
            {"event": "completed", "attempt_id": "a", "sent": True, "input_tokens": 20, "output_tokens": 6, "total_tokens": 26, "accepted": False},
            {"event": "completed", "attempt_id": "a", "sent": True, "input_tokens": 20, "output_tokens": 6, "total_tokens": 26},
        ])
        return {"pass": summary["requests"] == 1 and summary["total_tokens"] == 26,
                "requests": summary["requests"], "total_tokens": summary["total_tokens"]}
    if kind == "event_accept":
        spoken = 'Gate Guard says, "I do not know anything beyond the warning."'
        session = _base()
        note_completed_publication(session, text=spoken, gm={"metadata": {"expression_generation": {
            "decision": "adopted", "fallback_used": False, "candidate": "I do not know anything beyond the warning.",
            "delivered_generated": True,
        }}})
        event = record_completed_publication(
            {"gm_output": {"player_facing_text": spoken}}, source_handler="api_chat",
            publication_context=session["last_publication"], provider_rows=[{"sent": True, "attempt_id": "ok"}],
        )
        return {"pass": event["validation_outcome"] == "accepted_expression" and event["response_category"] == "dialogue",
                "validation": event["validation_outcome"], "category": event["response_category"]}
    if kind == "one_event":
        monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(tmp_path / "events.jsonl"))
        record_completed_publication({"gm_output": {"player_facing_text": FALLBACK}}, source_handler="api_chat",
                                     publication_context={"visible": FALLBACK, "owner": "completed_runtime_response"})
        lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
        return {"pass": len(lines) == 1, "lines": len(lines)}
    if kind == "mismatch":
        session = _base()
        record = note_completed_publication(session, text=FALLBACK, gm={"metadata": {"expression_generation": {
            "decision": "adopted", "fallback_used": False, "candidate": "A sentence the player did not see.",
            "delivered_generated": True,
        }}})
        return {"pass": record["dialogue_accepted"] is False, "dialogue_accepted": record["dialogue_accepted"]}
    return {"pass": False, "error": "unknown kind"}


def _ok(record, expect, session):
    visible = record["visible"]
    checks = []
    if "dialogue_accepted" in expect:
        checks.append(record["dialogue_accepted"] is expect["dialogue_accepted"])
    if "fallback" in expect:
        checks.append(record["fallback"] is expect["fallback"])
    if "validation" in expect:
        checks.append(record["validation_outcome"] == expect["validation"])
    if "owner" in expect:
        checks.append(record["owner"] == expect["owner"])
    if "advanced" in expect:
        checks.append(record["visible"] != ACCEPTED)
    if "exchange_matches" in expect:
        checks.append(session["conversational_context"]["last_gm_exchange"]["response"] == visible)
    if "expression_adopted" in expect:
        checks.append(session["last_background_expression"]["adopted"] is expect["expression_adopted"])
    if "stale_visible_replaced" in expect:
        checks.append(record["visible"] == FALLBACK)
    if "campaign_run_id" in expect:
        checks.append(record["campaign_run_id"] == expect["campaign_run_id"])
    if "turn" in expect:
        checks.append(record["turn"] == expect["turn"])
    for piece in expect.get("contains") or []:
        checks.append(piece.casefold() in visible.casefold())
    for piece in expect.get("excludes") or []:
        checks.append(piece.casefold() not in visible.casefold())
        checks.append(piece.casefold() not in json.dumps(record).casefold())
    return {"pass": all(checks), "visible": visible, "record": {k: record[k] for k in ("dialogue_accepted", "fallback", "validation_outcome", "owner", "turn", "campaign_run_id")}}
