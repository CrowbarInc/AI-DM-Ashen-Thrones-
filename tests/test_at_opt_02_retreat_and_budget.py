"""AT-OPT-02 provider-free routing and verification-budget regressions."""
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from game import storage
from game.bounded_improvisation import LEDGER_KEY
from game.physical_adjudication import disabled_retreat_skip, plan_physical
from game.provider_budget import ProviderBudgetRefused, admit_request, limits
from game.publication_contract import (
    ADJUDICATION_RESULT,
    FINAL_ENGINE_RESPONSE,
    OPERATIONAL_REFUSAL,
    UNSUPPORTED_ACTION,
    blocks_completed_publication,
    narration_skip,
    note_completed_publication,
    record_completed_publication,
    response_is_operational_refusal,
    stamp,
    stamp_budget_refusal,
)
from game.verification_budget import (
    DEFAULT_VERIFICATION_TOTAL_TOKENS,
    VerificationBudgetRejected,
    apply_verification_budget,
    resolve_verification_budget,
)
from tests.pr_play_79df3_harness import PRIOR, chat_turn, reset_budget
from tests.test_pr_play_76_physical import enable
from tests.test_pr_play_78_integrated import play
from tests.test_pr_play_79a_continuity import gate
from tests.test_pr_play_79c_publication import _physical, _yard

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
F3 = "I step back from the notice board."
REFUSAL = "That part is not supported here. It was not carried out."


def _narration(calls, *, forbid=False):
    def _call(*_args, **_kwargs):
        calls["n"] += 1
        if forbid:
            raise AssertionError("primary narration was dispatched")
        return {
            "player_facing_text": "The yard stays as it was.",
            "tags": ["deterministic_narration"],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "metadata": {"narration_provider_calls": 1},
        }

    return _call


def _route(text, session, scene, world):
    from game.api import deterministic_provider_skip_line

    return deterministic_provider_skip_line(
        resolution={"kind": "chat", "metadata": {}},
        scene=scene,
        world=world,
        session=session,
        player_text=text,
    )


def _usage(incoming, outgoing):
    return SimpleNamespace(
        usage=SimpleNamespace(
            input_tokens=incoming,
            output_tokens=outgoing,
            total_tokens=incoming + outgoing,
        ),
        id="fake-response",
        model="gpt-5.4-mini",
    )


def _prepare_budget(monkeypatch, tmp_path, **limits_kwargs):
    monkeypatch.delenv("ASHEN_DISABLE_PROVIDER_CALLS", raising=False)
    reset_budget(tmp_path / "usage.jsonl")
    for key, value in limits_kwargs.items():
        monkeypatch.setenv(key, str(value))


def test_f3_retreat_is_not_primary_narration_when_physical_is_disabled(tmp_path, monkeypatch):
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    calls = {"n": 0}
    monkeypatch.setattr("game.api.call_gpt", _narration(calls, forbid=True))
    result = chat_turn(tmp_path, monkeypatch, F3, interpret=False)
    session = storage.load_session()
    position = (session.get("bounded_improvisation_ledger") or {}).get("position") or {}
    assert calls["n"] == 0
    assert result["provider_calls"] == 0
    assert result["visible"] == REFUSAL
    assert result["operational"] is True
    assert result["refusal_category"] == "unresolved_retreat_without_adjudication"
    assert result["failure_stage"] == "routing"
    assert result["gameplay_publication_completed"] is False
    assert result["pointer_unchanged"] is True
    assert result["pointer_after"] == PRIOR
    assert result["turn_after"] == result["turn_before"]
    assert result["world_unchanged"] is True
    assert result["publication_events"] == []
    assert position.get("kind") != "back"


def test_natural_retreat_paraphrase_uses_the_same_refusal(tmp_path, monkeypatch):
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    calls = {"n": 0}
    monkeypatch.setattr("game.api.call_gpt", _narration(calls, forbid=True))
    result = chat_turn(tmp_path, monkeypatch, "I move back from the notice board.", interpret=False)
    assert calls["n"] == 0
    assert result["refusal_category"] == "unresolved_retreat_without_adjudication"
    assert result["operational"] is True
    assert result["turn_after"] == result["turn_before"]


def test_enabled_retreat_remains_on_the_physical_pathway(monkeypatch):
    enable(monkeypatch)
    session, scene = _yard()
    assert disabled_retreat_skip("I step back from the milestone.", session) is None
    _physical("I approach the milestone.", session, scene)
    plan, result, said = _physical("I step back from the milestone.", session, scene)
    assert plan["operation"] == "retreat"
    assert result["metadata"]["publication_contract"] == ADJUDICATION_RESULT
    assert result["metadata"]["skip_primary_narration"] is False
    assert result["state_changes"]["mutation"] is True
    assert session[LEDGER_KEY]["position"]["kind"] == "back"
    assert "step back" in said.casefold()
    packed = {"npcs": [], "world_state": {"flags": {}}}
    f3 = plan_physical(F3, session=session, scene=scene, world=packed)
    assert f3 is not None and f3["operation"] == "retreat"
    assert disabled_retreat_skip(F3, session) is None


def test_unrelated_unresolved_utterance_keeps_primary_narration_eligible(tmp_path, monkeypatch):
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    calls = {"n": 0}
    monkeypatch.setattr("game.api.call_gpt", _narration(calls))
    session, scene, world = gate()
    assert _route("I whistle at the clouds.", session, scene, world) is None
    result = chat_turn(tmp_path, monkeypatch, "I whistle at the clouds.", interpret=False)
    assert calls["n"] >= 1
    assert result["refusal_category"] != "unresolved_retreat_without_adjudication"
    assert result["visible"] != REFUSAL


def test_scene_information_stays_on_the_conversational_pathway(tmp_path, monkeypatch):
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    calls = {"n": 0}
    monkeypatch.setattr("game.api.call_gpt", _narration(calls, forbid=True))
    result = chat_turn(tmp_path, monkeypatch, "What can I see?", interpret=False)
    assert calls["n"] == 0
    assert result["visible"] != REFUSAL
    assert result["refusal_category"] != "unresolved_retreat_without_adjudication"
    assert result["operational"] is False


def test_greeting_is_not_reclassified_as_a_retreat(tmp_path, monkeypatch):
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    calls = {"n": 0}
    monkeypatch.setattr("game.api.call_gpt", _narration(calls))
    session, scene, world = gate()
    assert disabled_retreat_skip("Hello, Gate Guard.", session) is None
    assert _route("Hello, Gate Guard.", session, scene, world) is None
    result = chat_turn(tmp_path, monkeypatch, "Hello, Gate Guard.", interpret=False)
    assert result["visible"] != REFUSAL
    assert result["refusal_category"] != "unresolved_retreat_without_adjudication"


def test_enabled_dialogue_pathway_still_publishes_host_speech(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "1")
    session, scene, world = gate()
    _plan, result, said, _changed = play("Hello, Gate Guard.", session, scene, world)
    assert said != REFUSAL
    assert "says" in said.casefold()
    assert result["metadata"]["publication_contract"] == FINAL_ENGINE_RESPONSE
    assert result["metadata"]["skip_primary_narration"] is True


def test_ambiguous_step_back_reference_does_not_move_position(tmp_path, monkeypatch):
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    calls = {"n": 0}
    monkeypatch.setattr("game.api.call_gpt", _narration(calls))
    for text in (
        "They step back from the notice board.",
        "What if I step back from the notice board?",
        "I was thinking about stepping back from the notice board.",
    ):
        result = chat_turn(tmp_path, monkeypatch, text, interpret=False)
        session = storage.load_session()
        position = (session.get("bounded_improvisation_ledger") or {}).get("position") or {}
        assert result["refusal_category"] != "unresolved_retreat_without_adjudication"
        assert result["visible"] != REFUSAL
        assert position.get("kind") != "back"
    assert calls["n"] >= 1


def test_compound_and_directed_step_back_are_not_intercepted():
    session, scene, world = gate()
    for text in (
        "I step back to the tavern runner.",
        "I step back from the board and look around.",
        "The notice mentions stepping back from the road.",
    ):
        assert disabled_retreat_skip(text, session) is None
        assert _route(text, session, scene, world) is None


def test_owned_dialogue_publication_is_not_replaced_by_the_retreat_backstop():
    session, scene, world = gate()
    resolution = {"kind": "chat", "metadata": {}}
    stamp(resolution["metadata"], FINAL_ENGINE_RESPONSE, publication="The guard answers.")
    from game.api import deterministic_provider_skip_line

    routed = deterministic_provider_skip_line(
        resolution=resolution, scene=scene, world=world, session=session, player_text=F3
    )
    assert routed == ("The guard answers.", "publication_contract")
    assert narration_skip(resolution) == ("The guard answers.", "publication_contract")


def test_disabled_refusal_is_not_completed_gameplay(tmp_path, monkeypatch):
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    calls = {"n": 0}
    monkeypatch.setattr("game.api.call_gpt", _narration(calls, forbid=True))
    result = chat_turn(tmp_path, monkeypatch, F3, interpret=False)
    assert result["operational"] is True
    assert result["pointer_after"] == PRIOR
    assert result["publication_events"] == []
    recorded = record_completed_publication(
        result["body"],
        source_handler="api_chat",
        response_class=result["response_class"],
    )
    assert recorded is None


def test_verification_profile_installs_three_thousand_tokens(tmp_path, monkeypatch):
    _prepare_budget(monkeypatch, tmp_path)
    record = apply_verification_budget()
    assert record["total_tokens"] == DEFAULT_VERIFICATION_TOTAL_TOKENS == 3000
    assert record["source"] == "default"
    assert record["override"] is False
    ceiling = limits()
    assert ceiling is not None
    assert ceiling[3] == 3000
    assert ceiling[1] == 3000
    assert os.environ["ASHEN_VERIFICATION_BUDGET_SOURCE"] == "default"


def test_missing_malformed_and_historical_ceilings_do_not_become_two_hundred_thousand(tmp_path, monkeypatch):
    _prepare_budget(monkeypatch, tmp_path, ASHEN_PROVIDER_REQUEST_LIMIT="4", ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT="200000")
    apply_verification_budget()
    assert limits()[3] == 3000
    with pytest.raises(VerificationBudgetRejected):
        apply_verification_budget(total="not-a-number")
    assert limits()[3] == 3000
    with pytest.raises(VerificationBudgetRejected):
        apply_verification_budget(total=200000)
    assert limits()[3] == 3000
    monkeypatch.delenv("ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT", raising=False)
    with pytest.raises(VerificationBudgetRejected):
        resolve_verification_budget(total="")
    assert os.environ.get("ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT") != "200000"


def test_explicit_override_is_recorded(tmp_path, monkeypatch):
    _prepare_budget(monkeypatch, tmp_path)
    record = apply_verification_budget(override=8000)
    assert record["override"] is True
    assert record["source"] == "override"
    assert record["total_tokens"] == 8000
    assert limits()[3] == 8000
    assert os.environ["ASHEN_VERIFICATION_BUDGET_SOURCE"] == "override"
    historical = apply_verification_budget(override=200000)
    assert historical["override"] is True
    assert historical["total_tokens"] == 200000
    assert limits()[3] == 200000


def test_oversized_estimate_is_refused_before_dispatch(tmp_path, monkeypatch):
    _prepare_budget(
        monkeypatch,
        tmp_path,
        ASHEN_PROVIDER_REQUEST_LIMIT="4",
        ASHEN_PROVIDER_INPUT_TOKEN_LIMIT="3000",
        ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT="600",
        ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT="3000",
    )
    sent = {"n": 0}

    def invoke():
        sent["n"] += 1
        return _usage(1, 1)

    attempt = admit_request(purpose="primary_turn", owner="gm.call_gpt", estimated_input=28000, max_output=600)
    assert attempt.refusal == "input-token ceiling"
    with pytest.raises(ProviderBudgetRefused):
        attempt.dispatch(invoke)
    assert sent["n"] == 0
    assert attempt.dispatched is False
    assert attempt.estimated_input == 28000


def test_within_budget_request_reaches_the_provider_boundary(tmp_path, monkeypatch):
    _prepare_budget(
        monkeypatch,
        tmp_path,
        ASHEN_PROVIDER_REQUEST_LIMIT="4",
        ASHEN_PROVIDER_INPUT_TOKEN_LIMIT="3000",
        ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT="600",
        ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT="3000",
    )
    sent = {"n": 0}

    def invoke():
        sent["n"] += 1
        return _usage(11, 3)

    attempt = admit_request(purpose="expression", owner="integrated_play", estimated_input=100, max_output=40)
    response = attempt.dispatch(invoke)
    assert sent["n"] == 1
    assert attempt.dispatched is True
    assert attempt.estimated_input == 100
    assert response.usage.total_tokens == 14
    assert attempt.completed["total_tokens"] == 14
    assert attempt.completed["input_tokens"] == 11
    assert attempt.completed["sent"] is True


def test_aggregate_budget_exhaustion_refuses_the_next_request(tmp_path, monkeypatch):
    _prepare_budget(
        monkeypatch,
        tmp_path,
        ASHEN_PROVIDER_REQUEST_LIMIT="4",
        ASHEN_PROVIDER_INPUT_TOKEN_LIMIT="3000",
        ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT="600",
        ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT="500",
    )
    sent = {"n": 0}

    def invoke():
        sent["n"] += 1
        return _usage(200, 40)

    for _ in range(2):
        attempt = admit_request(purpose="expression", owner="integrated_play", estimated_input=200, max_output=40)
        attempt.dispatch(invoke)
    later = admit_request(purpose="expression", owner="integrated_play", estimated_input=200, max_output=40)
    assert later.refusal == "total-token ceiling"
    with pytest.raises(ProviderBudgetRefused):
        later.dispatch(invoke)
    assert sent["n"] == 2
    assert later.dispatched is False


def test_budget_refusal_is_not_completed_gameplay(tmp_path):
    session = {"last_publication": {"visible": PRIOR, "turn": 2}}
    gm = {
        "player_facing_text": (
            "The action was resolved, but live narration was not requested "
            "because it would exceed the provider budget."
        ),
        "tags": ["provider_budget_refused"],
        "metadata": {"provider_budget_refusal": "total-token ceiling"},
    }
    resolution = {"kind": "chat", "metadata": {}}
    stamp_budget_refusal(resolution, gm)
    assert resolution["metadata"]["response_class"] == OPERATIONAL_REFUSAL
    assert resolution["metadata"]["gameplay_publication_completed"] is False
    assert blocks_completed_publication(resolution, gm)
    assert response_is_operational_refusal({"resolution": resolution, "gm_output": gm})
    assert note_completed_publication(
        session, text=gm["player_facing_text"], resolution=resolution, gm=gm
    ) is None
    assert session["last_publication"]["visible"] == PRIOR
    assert record_completed_publication(
        {"gm_output": gm, "resolution": resolution},
        source_handler="api_chat",
        response_class=OPERATIONAL_REFUSAL,
    ) is None
    assert not (tmp_path / "events.jsonl").exists()


def test_retreat_refusal_stamp_is_unsupported_and_operational():
    from game.api import deterministic_provider_skip_line

    session, scene, world = gate()
    resolution = {"kind": "chat", "metadata": {}}
    routed = deterministic_provider_skip_line(
        resolution=resolution, scene=scene, world=world, session=session, player_text=F3
    )
    assert routed == (REFUSAL, "unresolved_retreat_without_adjudication")
    meta = resolution["metadata"]
    assert meta["publication_contract"] == UNSUPPORTED_ACTION
    assert meta["response_class"] == OPERATIONAL_REFUSAL
    assert meta["gameplay_executed"] is False
    assert blocks_completed_publication(resolution) is True


def test_http_script_uses_the_verification_profile():
    source = (ROOT / "artifacts" / "pr_play_79df3" / "http_acceptance.py").read_text(encoding="utf-8")
    assert "apply_verification_budget()" in source
    assert "200000" not in source
