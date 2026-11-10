"""PR-PLAY-79D-F development checks for expression settlement and publication."""
import copy

import pytest

from tests.pr_play_79df_executor import (
    ACCEPTED, DIRECTION, HIDDEN, IRRELEVANT,
    cross_campaign, dialogue, physical, protected_write_blocked,
    provider_accounting, provider_admission, renderer, snapshot_recall,
    stale_owner_not_applied,
)


def test_accepted_expression_is_one_settled_publication(monkeypatch):
    actual = physical(monkeypatch, ACCEPTED, narrate=True, second_skip=True)
    assert actual["calls"] == 1
    assert actual["live"] is True
    assert actual["contract"] == "FINAL_ENGINE_RESPONSE"
    assert actual["facts_committed"] is True
    assert "beside" in actual["published"].casefold()
    assert actual["position"] == "beside"
    assert actual["target"] == "notice_board"


@pytest.mark.parametrize("transport,reason,banned", [
    (IRRELEVANT, "irrelevant", "distant"),
    (HIDDEN, "consequential_or_hidden", "secret"),
    (DIRECTION, "unestablished_direction", "northwest"),
])
def test_rejected_expression_falls_back_once(monkeypatch, transport, reason, banned):
    actual = physical(monkeypatch, transport, narrate=True, second_skip=True)
    assert actual["calls"] == 1
    assert actual["live"] is False
    assert reason in actual["reasons"]
    assert banned not in actual["published"].casefold()
    assert actual["contract"] == "FINAL_ENGINE_RESPONSE"
    assert "beside" in actual["published"].casefold()


def test_closed_gate_makes_no_expression_request(monkeypatch):
    actual = physical(monkeypatch, ACCEPTED, narrate=False)
    assert actual["calls"] == 0
    assert actual["live"] is False
    assert "stop there" not in actual["published"].casefold()
    assert "beside" in actual["published"].casefold()


def test_dialogue_speech_is_not_replaced(monkeypatch):
    greeting = dialogue(monkeypatch, "Hello, Gate Guard.")
    question = dialogue(monkeypatch, "What do you know about the missing patrol?", establish=True)
    assert "hello" in greeting["said"].casefold()
    assert "which person" not in greeting["said"].casefold()
    assert "CANARY" not in greeting["said"]
    assert greeting["calls"] == 0
    assert question["said"].strip()
    assert "which person" not in question["said"].casefold()
    assert "CANARY" not in question["said"]


def test_renderer_does_not_mutate_resolution(monkeypatch):
    actual = renderer(monkeypatch)
    assert actual["unchanged"] is True
    assert actual["same_text"] is True
    assert "four moons" in actual["published"]


def test_cross_campaign_object_is_not_visible(monkeypatch):
    actual = cross_campaign(monkeypatch)
    assert actual["plan_is_none"] is True
    assert actual["targets_alpha"] is False
    assert actual["beta_unchanged"] is True


def test_snapshot_restores_disclosed_fact(tmp_path, monkeypatch):
    actual = snapshot_recall(tmp_path, monkeypatch)
    assert actual["knowledge_restored"] is True
    assert "northwest mud track" in actual["repeat_text"]
    assert actual["publication_lines"] >= 1


def test_stale_dialogue_owner_is_not_applied(tmp_path, monkeypatch):
    actual = stale_owner_not_applied(tmp_path, monkeypatch)
    assert actual["stale_dialogue_owner"] is False
    assert actual["category"] == "live_narration"
    assert actual["validation"] == "accepted_expression"
    assert actual["attempts"] == ["expr-1"]


def test_provider_accounting_counts_completed_attempts_once():
    actual = provider_accounting()
    assert actual["requests"] == 2
    assert actual["retries"] == 1
    assert actual["fallbacks"] == 1
    assert actual["total_tokens"] == 18


def test_provider_admission_stops_at_request_ceiling(monkeypatch):
    actual = provider_admission(monkeypatch)
    assert actual["refusal"] == "request ceiling"


def test_protected_campaign_write_is_blocked():
    actual = protected_write_blocked()
    assert actual["blocked"] is True


def test_authoritative_position_matches_publication(monkeypatch):
    before_calls = []
    actual = physical(monkeypatch, ACCEPTED)
    resolution = actual["resolution"]
    untouched = copy.deepcopy(resolution)
    from game.publication_contract import narration_skip
    narration_skip(resolution)
    assert resolution == untouched
    assert actual["position"] == "beside"
    assert "discover" not in actual["published"].casefold()
    before_calls.append(actual["calls"])
    assert before_calls == [1]
