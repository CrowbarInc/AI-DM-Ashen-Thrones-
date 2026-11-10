"""PR-PLAY-79D-F2 publication-state consistency.

Development checks. The frozen holdout is a separate file and is not this module.
"""
import copy
import json

import pytest
from fastapi.testclient import TestClient

from game.dialogue_authority import remember_dialogue_commitment
from game.expressive_dialogue import set_expression_transport
from game.publication_contract import (
    note_completed_publication,
    record_completed_publication,
    summarize_provider_rows,
)
from game import api, storage


ACCEPTED = 'Gate Guard says, "The notice board does mention a missing patrol, but I don\'t have any details beyond that."'
FALLBACK = 'Gate Guard mutters, "Word is, check the notice board."'
HIDDEN = "The missing patrol was last seen taking the northwest mud track past the crates."


def _session(visible=ACCEPTED, *, accepted=True, turn=4, campaign="alpha"):
    return {
        "campaign_run_id": campaign,
        "turn_counter": turn,
        "conversational_context": {
            "last_gm_exchange": {"response": visible, "owner": "GM"},
        },
        "last_background_expression": {
            "adopted": accepted,
            "candidate": "The notice board does mention a missing patrol.",
            "decision": "adopted" if accepted else "rejected",
        },
        "last_narration": {"adopted": False, "candidate": "", "reasons": ["dialogue_already_final"]},
        "last_publication": {
            "owner": "integrated_play.commit_integrated",
            "contract": "FINAL_ENGINE_RESPONSE",
            "final": True,
            "dialogue_generated": True,
            "dialogue_accepted": accepted,
            "dialogue_composed": True,
            "dialogue_published": True,
            "narration_requested": False,
            "narration_accepted": False,
            "narration_published": False,
            "visible": visible,
            "turn": turn,
            "campaign_run_id": campaign,
        },
        "world_state": {"flags": {"patrol_survey": False}},
    }


def _rejected_gm(candidate="They took the northwest tunnel and the king paid them."):
    return {
        "player_facing_text": FALLBACK,
        "metadata": {
            "expression_generation": {
                "decision": "rejected",
                "fallback_used": True,
                "candidate": candidate,
                "delivered_generated": False,
            }
        },
    }


def test_latest_publication_advances_on_fallback():
    session = _session()
    record = note_completed_publication(session, text=FALLBACK, gm=_rejected_gm(), resolution={"kind": "question"})
    assert record["visible"] == FALLBACK
    assert record["turn"] == 4
    assert record["campaign_run_id"] == "alpha"
    assert record["dialogue_published"] is True
    assert record["dialogue_accepted"] is False
    assert record["fallback"] is True
    assert record["validation_outcome"] == "engine_or_grounded_fallback"
    assert record["owner"] == "completed_runtime_response"
    assert record["expression_decision"] == "rejected"
    assert "northwest" not in json.dumps(record)
    assert "king" not in json.dumps(record)
    assert session["last_publication"] is record
    assert session["conversational_context"]["last_gm_exchange"]["response"] == FALLBACK


def test_stale_acceptance_is_not_attached_to_fallback():
    session = _session()
    note_completed_publication(session, text=FALLBACK, gm=_rejected_gm())
    assert session["last_publication"]["dialogue_accepted"] is False
    assert session["last_background_expression"]["adopted"] is False
    assert session["last_background_expression"]["candidate"].startswith("They took")
    assert session["last_publication"]["visible"] != ACCEPTED


def test_matching_composer_record_keeps_accepted_provenance():
    session = _session(visible='Gate Guard says, "Evening."', accepted=True, turn=6)
    note_completed_publication(session, text='Gate Guard says, "Evening."')
    kept = session["last_publication"]
    assert kept["owner"] == "integrated_play.commit_integrated"
    assert kept["dialogue_accepted"] is True
    assert kept["dialogue_published"] is True
    assert kept["visible"] == 'Gate Guard says, "Evening."'
    assert kept["turn"] == 6


def test_rejected_repeat_of_the_same_sentence_is_not_still_accepted():
    session = _session(visible=FALLBACK, accepted=True)
    note_completed_publication(session, text=FALLBACK, gm=_rejected_gm())
    assert session["last_publication"]["dialogue_accepted"] is False
    assert session["last_publication"]["fallback"] is True
    assert session["last_publication"]["owner"] == "completed_runtime_response"


def test_empty_text_does_not_clear_the_latest_record():
    session = _session()
    assert note_completed_publication(session, text="  ") is None
    assert session["last_publication"]["visible"] == ACCEPTED


def test_accepted_expression_sets_dialogue_provenance():
    spoken = 'Gate Guard says, "I do not know anything beyond the warning about a missing patrol."'
    session = _session()
    gm = {
        "metadata": {
            "expression_generation": {
                "decision": "adopted",
                "fallback_used": False,
                "candidate": "I do not know anything beyond the warning about a missing patrol.",
                "delivered_generated": True,
            }
        }
    }
    record = note_completed_publication(session, text=spoken, gm=gm)
    assert record["dialogue_accepted"] is True
    assert record["dialogue_published"] is True
    assert record["fallback"] is False
    assert record["validation_outcome"] == "accepted_expression"
    assert record["expression_decision"] == "adopted"
    assert session["last_background_expression"]["adopted"] is True
    assert HIDDEN not in spoken


def test_accepted_candidate_must_be_inside_the_visible_sentence():
    session = _session()
    gm = {
        "metadata": {
            "expression_generation": {
                "decision": "adopted",
                "fallback_used": False,
                "candidate": "A different sentence the player never saw.",
                "delivered_generated": True,
            }
        }
    }
    record = note_completed_publication(session, text=FALLBACK, gm=gm)
    assert record["dialogue_accepted"] is False
    assert record["visible"] == FALLBACK


def test_narration_acceptance_is_not_applied_to_speech():
    session = _session()
    session["last_narration"] = {"adopted": True, "candidate": "You take a step backward away from the Notice board."}
    record = note_completed_publication(session, text=FALLBACK, gm=_rejected_gm())
    assert record["narration_accepted"] is False
    assert record["narration_published"] is False
    assert record["dialogue_published"] is True


def test_accepted_physical_narration_is_the_latest_publication():
    line = "You take a step backward away from the Notice board."
    session = _session(visible=ACCEPTED)
    session["turn_counter"] = 9
    session["last_narration"] = {"adopted": True, "candidate": line}
    record = note_completed_publication(
        session,
        text=line,
        resolution={"kind": "interact", "metadata": {"publication_contract": "FINAL_ENGINE_RESPONSE", "engine_publication": line}},
    )
    assert record["visible"] == line
    assert record["narration_accepted"] is True
    assert record["narration_published"] is True
    assert record["dialogue_published"] is False
    assert record["validation_outcome"] == "accepted_expression"
    assert record["contract"] == "FINAL_ENGINE_RESPONSE"
    assert record["turn"] == 9


def test_rejected_narration_stays_a_grounded_fallback():
    line = "You move beside the notice board."
    session = _session()
    session["last_narration"] = {"adopted": False, "candidate": "Rain keeps falling on the distant hills."}
    record = note_completed_publication(session, text=line)
    assert record["narration_accepted"] is False
    assert record["fallback"] is True
    assert record["visible"] == line
    assert "distant hills" not in record["visible"]


def test_publication_event_uses_the_completed_sentence():
    session = _session()
    note_completed_publication(session, text=FALLBACK, gm=_rejected_gm())
    row = record_completed_publication(
        {"gm_output": {"player_facing_text": FALLBACK}},
        source_handler="api_chat",
        publication_context=session["last_publication"],
        provider_rows=[{"sent": True, "attempt_id": "expr-rejected"}],
        presentation_rows=[{"kind": "dialogue", "decision": "rejected", "text": "They took the northwest tunnel."}],
    )
    assert row["final_player_facing_response"] == FALLBACK
    assert row["publication_owner"] == "completed_runtime_response"
    assert row["validation_outcome"] == "engine_or_grounded_fallback"
    assert row["accepted_expression_references"] == []
    assert row["response_category"] == "engine_response"


def test_publication_event_accepts_only_the_visible_expression():
    spoken = 'Gate Guard says, "I do not know anything beyond the warning."'
    session = _session()
    gm = {"metadata": {"expression_generation": {
        "decision": "adopted", "fallback_used": False,
        "candidate": "I do not know anything beyond the warning.", "delivered_generated": True,
    }}}
    note_completed_publication(session, text=spoken, gm=gm)
    row = record_completed_publication(
        {"gm_output": {"player_facing_text": spoken}},
        source_handler="api_chat",
        publication_context=session["last_publication"],
        provider_rows=[{"sent": True, "attempt_id": "expr-ok"}],
    )
    assert row["validation_outcome"] == "accepted_expression"
    assert row["response_category"] == "dialogue"
    assert row["publication_owner"] == "completed_runtime_response"
    assert row["accepted_expression_references"]
    assert row["provider_attempt_references"] == ["expr-ok"]


def test_one_call_writes_one_publication_event(tmp_path, monkeypatch):
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(tmp_path / "events.jsonl"))
    record_completed_publication(
        {"gm_output": {"player_facing_text": FALLBACK}},
        source_handler="api_chat",
        publication_context={"visible": FALLBACK, "owner": "completed_runtime_response", "dialogue_accepted": False},
    )
    lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["final_player_facing_response"] == FALLBACK


def test_save_and_reload_keep_the_fallback_pointer(tmp_path, monkeypatch):
    from tests.test_pr_play_52_quarantined_integration import _seed

    _seed(tmp_path, monkeypatch, "frontier_gate")
    session = storage.load_session()
    session["turn_counter"] = 16
    note_completed_publication(session, text=FALLBACK, gm=_rejected_gm())
    storage.save_session(session)
    restored = storage.load_session()
    assert restored["last_publication"]["visible"] == FALLBACK
    assert restored["last_publication"]["dialogue_accepted"] is False
    assert restored["last_publication"]["campaign_run_id"] == session["campaign_run_id"]
    assert restored["campaign_run_id"] == session["campaign_run_id"]


def test_cross_session_publication_does_not_leak():
    first = _session(campaign="alpha")
    second = _session(visible="Serjeant says, \"Hold.\"", campaign="beta", turn=1)
    note_completed_publication(first, text=FALLBACK, gm=_rejected_gm())
    assert second["last_publication"]["visible"] == "Serjeant says, \"Hold.\""
    assert second["last_publication"]["campaign_run_id"] == "beta"
    assert first["last_publication"]["campaign_run_id"] == "alpha"


def test_note_does_not_invent_world_truth():
    session = _session()
    before = copy.deepcopy(session["world_state"])
    note_completed_publication(session, text=FALLBACK, gm=_rejected_gm(HIDDEN))
    assert session["world_state"] == before
    assert HIDDEN not in session["last_publication"]["visible"]
    blob = json.dumps(session["last_publication"])
    assert "northwest" not in blob


def test_dialogue_commitment_stays_noncanonical():
    session = _session()
    social = {
        "npc_id": "gate_guard",
        "npc_name": "Gate Guard",
        "dialogue_authority": {
            "npc_id": "gate_guard",
            "knowledge_posture": "unknown",
            "subject": "notice board",
            "authorized_proposition": "",
        },
    }
    entry = remember_dialogue_commitment(session, social=social, player_text="What does the board say?", line=FALLBACK, turn=16)
    assert entry["canonical"] is False
    assert entry["text"] == FALLBACK
    assert session["world_state"]["flags"] == {"patrol_survey": False}


def test_uncertainty_commitment_is_not_an_established_fact():
    session = _session()
    line = 'Gate Guard says, "I am not certain. I do not know about that."'
    social = {"npc_id": "gate_guard", "dialogue_authority": {
        "npc_id": "gate_guard", "knowledge_posture": "partial", "subject": "patrol", "authorized_proposition": "",
    }}
    entry = remember_dialogue_commitment(session, social=social, player_text="Is the patrol lost?", line=line, turn=5)
    assert entry["kind"] == "partial_answer"
    assert entry["canonical"] is False
    record = note_completed_publication(session, text=line)
    assert record["fallback"] is True
    assert record["dialogue_accepted"] is False


def test_established_posture_is_not_stored_as_a_new_commitment():
    session = _session()
    before = copy.deepcopy(session.get("conversational_context"))
    social = {"npc_id": "gate_guard", "dialogue_authority": {"knowledge_posture": "established", "npc_id": "gate_guard", "subject": "board"}}
    assert remember_dialogue_commitment(session, social=social, player_text="Again?", line=FALLBACK, turn=3) is None
    assert session["conversational_context"]["last_gm_exchange"] == before["last_gm_exchange"]


def test_provider_accounting_counts_one_rejected_expression():
    summary = summarize_provider_rows([
        {"event": "admitted", "attempt_id": "a", "sent": True},
        {"event": "completed", "attempt_id": "a", "sent": True, "input_tokens": 20, "output_tokens": 6, "total_tokens": 26, "accepted": False},
        {"event": "completed", "attempt_id": "a", "sent": True, "input_tokens": 20, "output_tokens": 6, "total_tokens": 26},
    ])
    assert summary["requests"] == 1
    assert summary["input_tokens"] == 20
    assert summary["output_tokens"] == 6
    assert summary["total_tokens"] == 26
    assert summary["retries"] == 0


def test_provider_admission_refusal_is_not_a_publication(monkeypatch):
    import tempfile
    from pathlib import Path
    import game.provider_budget as budget

    saved = (
        budget._REQUESTS, budget._STOPPED, budget._STOP_REASON, budget._INITIALIZED,
        budget._INPUT, budget._OUTPUT, budget._RESERVED_INPUT, budget._RESERVED_OUTPUT,
        budget._LEDGER_PATH,
    )
    events = list(budget._EVENTS)
    attempts = dict(budget._ATTEMPTS)
    monkeypatch.setenv("ASHEN_PROVIDER_USAGE_PATH", str(Path(tempfile.mkdtemp()) / "usage.jsonl"))
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
    try:
        attempt = budget.admit_request(purpose="expression", owner="pr_play_79df2", estimated_input=1, max_output=1, attempt_id="79df2")
        assert attempt.refusal
        assert attempt.dispatched is False
    finally:
        (
            budget._REQUESTS, budget._STOPPED, budget._STOP_REASON, budget._INITIALIZED,
            budget._INPUT, budget._OUTPUT, budget._RESERVED_INPUT, budget._RESERVED_OUTPUT,
            budget._LEDGER_PATH,
        ) = saved
        budget._EVENTS[:] = events
        budget._ATTEMPTS.clear()
        budget._ATTEMPTS.update(attempts)


def test_physical_narration_still_uses_one_expression(monkeypatch):
    from tests.pr_play_79df_executor import ACCEPTED as LINE
    from tests.pr_play_79df_executor import physical

    acted = physical(monkeypatch, LINE, narrate=True)
    assert acted["calls"] == 1
    assert acted["live"] is True
    assert acted["contract"] == "FINAL_ENGINE_RESPONSE"
    session = {"campaign_run_id": "alpha", "turn_counter": 2, "last_narration": {"adopted": True, "candidate": acted["published"]}}
    record = note_completed_publication(session, text=acted["published"])
    assert record["visible"] == acted["published"]
    assert record["narration_published"] is True


def test_second_narration_skip_does_not_call_expression_again(monkeypatch):
    from tests.pr_play_79df_executor import ACCEPTED as LINE
    from tests.pr_play_79df_executor import physical

    acted = physical(monkeypatch, LINE, narrate=True, second_skip=True)
    assert acted["calls"] == 1
    assert acted["live"] is True


def test_irrelevant_narration_is_not_published(monkeypatch):
    from tests.pr_play_79df_executor import IRRELEVANT, physical

    acted = physical(monkeypatch, IRRELEVANT, narrate=True)
    assert acted["calls"] == 1
    assert acted["live"] is False
    assert "distant" not in acted["published"].casefold()


def test_hidden_narration_is_not_published(monkeypatch):
    from tests.pr_play_79df_executor import HIDDEN as SECRET
    from tests.pr_play_79df_executor import physical

    acted = physical(monkeypatch, SECRET, narrate=True)
    assert "secret" not in acted["published"].casefold()
    assert acted["live"] is False


def test_recall_returns_only_the_disclosed_fact():
    from tests.test_pr_play_79d_closeout import exercise_recall

    assert exercise_recall("chart", "The chart records four moons.", "known") == ("The chart records four moons.",)
    assert exercise_recall("chart", "The chart records four moons.", "hidden") == ()
    assert exercise_recall("chart", "The chart records four moons.", "other_source") == ()
    assert exercise_recall("plaque", "The plaque names the mason Eda.", "wrong_scene") == ()


def test_renderer_recall_does_not_mutate_resolution(monkeypatch):
    from tests.pr_play_79df_executor import renderer

    result = renderer(monkeypatch)
    assert result["unchanged"] is True
    assert result["same_text"] is True
    assert "four moons" in result["published"]


def test_cross_campaign_physical_plan_does_not_mutate_the_other_session(monkeypatch):
    from tests.pr_play_79df_executor import cross_campaign

    result = cross_campaign(monkeypatch)
    assert result["plan_is_none"] is True
    assert result["beta_unchanged"] is True
    assert result["targets_alpha"] is False


def test_duplicate_chat_does_not_write_a_second_event(tmp_path, monkeypatch):
    from tests.test_pr_play_62_investigation_quality import setup_session

    setup_session(tmp_path, monkeypatch)
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(tmp_path / "events.jsonl"))
    client = TestClient(api.app)
    client.__enter__()
    try:
        first = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board.", "client_request_id": "same-turn"})
        second = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board.", "client_request_id": "same-turn"})
    finally:
        client.__exit__(None, None, None)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["gm_output"]["player_facing_text"] == second.json()["gm_output"]["player_facing_text"]
    lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    body = first.json()["gm_output"]["player_facing_text"]
    assert storage.load_session()["last_publication"]["visible"] == body
    assert "northwest" in body or "nothing new" in body.casefold() or "notice" in body.casefold()


def test_http_fallback_advances_latest_publication(tmp_path, monkeypatch):
    from tests.test_pr_play_62_investigation_quality import setup_session

    setup_session(tmp_path, monkeypatch)
    monkeypatch.delenv("ASHEN_DISABLE_EXPRESSION_GENERATION", raising=False)
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(tmp_path / "events.jsonl"))
    session = storage.load_session()
    session["last_publication"] = {
        "owner": "integrated_play.commit_integrated",
        "contract": "FINAL_ENGINE_RESPONSE",
        "final": True,
        "dialogue_accepted": True,
        "dialogue_published": True,
        "visible": ACCEPTED,
            "turn": 1,
            "campaign_run_id": session.get("campaign_run_id"),
    }
    storage.save_session(session)
    flags_before = copy.deepcopy((storage.load_world().get("world_state") or {}).get("flags") or {})

    def _bad(_contract):
        return "They were last seen taking the northwest mud track, and the king paid them."

    set_expression_transport(_bad)
    client = TestClient(api.app)
    client.__enter__()
    try:
        response = client.post(
            "/api/chat?ui_mode=player",
            json={"text": "Gate Guard, what does the notice board say about the patrol?"},
        )
    finally:
        set_expression_transport(None)
        client.__exit__(None, None, None)
    assert response.status_code == 200
    visible = response.json()["gm_output"]["player_facing_text"]
    assert "king paid" not in visible.casefold()
    loaded = storage.load_session()
    assert loaded["last_publication"]["visible"] == visible
    assert loaded["last_publication"]["dialogue_accepted"] is False
    assert loaded["last_publication"]["visible"] != ACCEPTED
    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert event["final_player_facing_response"] == visible
    assert event["validation_outcome"] == "engine_or_grounded_fallback"
    assert event["accepted_expression_references"] == []
    flags_after = (storage.load_world().get("world_state") or {}).get("flags") or {}
    assert flags_after == flags_before


def test_http_save_reload_matches_transcript(tmp_path, monkeypatch):
    from tests.test_pr_play_62_investigation_quality import setup_session

    setup_session(tmp_path, monkeypatch)
    client = TestClient(api.app)
    client.__enter__()
    try:
        response = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board."})
        visible = response.json()["gm_output"]["player_facing_text"]
        snapshot = storage.create_snapshot("79df2 publication")
        storage.load_snapshot(snapshot["id"])
        reloaded = storage.load_session()
    finally:
        client.__exit__(None, None, None)
    assert reloaded["last_publication"]["visible"] == visible
    log = storage.load_log()
    assert log[-1]["gm_output"]["player_facing_text"] == visible
    assert HIDDEN not in visible or "Previously disclosed" in visible or "northwest" in visible


def test_player_projection_omits_resolution_internals(tmp_path, monkeypatch):
    from tests.test_pr_play_62_investigation_quality import setup_session

    setup_session(tmp_path, monkeypatch)
    client = TestClient(api.app)
    client.__enter__()
    try:
        response = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board."})
    finally:
        client.__exit__(None, None, None)
    body = response.json()
    assert body.get("resolution") == {}
    assert "hidden_facts" not in json.dumps(body)
    assert body["gm_output"]["player_facing_text"]


def test_protected_data_write_is_blocked():
    from tests.helpers.storage_isolation import PROTECTED

    target = PROTECTED / "campaign.json"
    with pytest.raises(PermissionError):
        open(target, "a", encoding="utf-8")


@pytest.mark.parametrize(
    "text,accepted",
    [
        ('Gate Guard says, "I do not know about that."', False),
        ('Gate Guard mutters, "Word is, check the notice board."', False),
        ("You take a step backward away from the Notice board.", False),
    ],
)
def test_pointer_matches_visible_text(text, accepted):
    session = _session()
    record = note_completed_publication(session, text=text)
    assert record["visible"] == text
    assert record["dialogue_accepted"] is accepted
    assert session["last_publication"]["campaign_run_id"] == "alpha"
