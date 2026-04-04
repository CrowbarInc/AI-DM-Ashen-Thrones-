"""Unit tests for synthetic runner scaffold (harness only)."""
from __future__ import annotations

import importlib
import sys

import pytest

from tests.helpers.synthetic_types import SyntheticDecision, SyntheticProfile, SyntheticRunResult

pytestmark = [pytest.mark.unit, pytest.mark.synthetic]


def test_run_placeholder_session_returns_result():
    from tests.helpers.synthetic_runner import run_placeholder_session

    result = run_placeholder_session(max_turns=0)
    assert isinstance(result, SyntheticRunResult)
    assert result.ok is True
    assert len(result.profiles) == 1
    assert isinstance(result.profiles[0], SyntheticProfile)
    assert result.profiles[0].profile_id == "placeholder"
    assert result.profile_name == "placeholder"
    assert result.seed == 0
    assert result.stop_reason == "max_turns_reached"


def test_import_synthetic_runner_has_no_top_level_game_imports():
    before = {name for name in sys.modules if name == "game" or name.startswith("game.")}
    before_transcript = "tests.helpers.transcript_runner" in sys.modules
    sys.modules.pop("tests.helpers.synthetic_runner", None)

    importlib.import_module("tests.helpers.synthetic_runner")

    after = {name for name in sys.modules if name == "game" or name.startswith("game.")}
    assert after == before
    assert ("tests.helpers.transcript_runner" in sys.modules) is before_transcript


def test_run_placeholder_session_fake_gm_is_deterministic_and_non_empty():
    from tests.helpers.synthetic_runner import run_placeholder_session

    result_a = run_placeholder_session(max_turns=2, seed=41, use_fake_gm=True)
    result_b = run_placeholder_session(max_turns=2, seed=41, use_fake_gm=True)

    assert result_a.ok is True
    assert result_a.decisions == result_b.decisions
    assert result_a.snapshots == result_b.snapshots
    assert len(result_a.snapshots) == 2
    assert all(decision.player_text.strip() for decision in result_a.decisions)
    assert all(
        snapshot["response"]["player_facing_text"].strip()
        for snapshot in result_a.snapshots
    )


def _prod_like_model_call(*_args: object, **_kwargs: object) -> dict[str, str]:
    return {"player_facing_text": "original"}


def test_run_placeholder_session_can_patch_fake_gm_without_production_changes(monkeypatch: pytest.MonkeyPatch):
    from tests.helpers.synthetic_runner import run_placeholder_session

    target = f"{__name__}._prod_like_model_call"
    _ = run_placeholder_session(
        max_turns=1,
        player_texts=("hello there",),
        use_fake_gm=True,
        monkeypatch=monkeypatch,
        fake_gm_patch_targets=(target,),
    )

    patched = _prod_like_model_call("hello there")
    assert patched["source"] == "synthetic_fake_gm"
    assert patched["player_facing_text"].strip()


def test_run_placeholder_session_stops_on_max_turns():
    from tests.helpers.synthetic_runner import run_placeholder_session

    result = run_placeholder_session(max_turns=3, seed=7, use_fake_gm=True)
    assert len(result.decisions) == 3
    assert result.stop_reason == "max_turns_reached"


def _stalling_policy(_view: object) -> SyntheticDecision:
    return SyntheticDecision(player_text="I wait.", rationale="stall")


def test_run_placeholder_session_stops_on_repeated_stall_threshold():
    from tests.helpers.synthetic_runner import run_placeholder_session

    result = run_placeholder_session(
        max_turns=8,
        seed=9,
        use_fake_gm=True,
        policy_fn=_stalling_policy,
        stall_repeat_threshold=3,
    )
    assert result.stop_reason == "stall_repeat_threshold"
    assert len(result.decisions) == 3


def test_run_placeholder_session_non_placeholder_run_has_no_empty_player_inputs():
    from tests.helpers.synthetic_runner import run_placeholder_session

    result = run_placeholder_session(max_turns=4, seed=123, use_fake_gm=True)
    assert len(result.decisions) == 4
    assert all(decision.player_text.strip() for decision in result.decisions)


def _stop_policy(_view: object) -> SyntheticDecision:
    return SyntheticDecision(
        player_text="I end the experiment now.",
        rationale="manual_stop",
        stop_requested=True,
        stop_reason="policy_stop",
    )


def test_run_placeholder_session_supports_explicit_policy_stop_signal():
    from tests.helpers.synthetic_runner import run_placeholder_session

    result = run_placeholder_session(max_turns=10, use_fake_gm=True, policy_fn=_stop_policy)
    assert len(result.decisions) == 1
    assert result.stop_reason == "policy_stop"


def test_run_synthetic_session_fake_gm_returns_turn_views():
    from tests.helpers.synthetic_runner import run_synthetic_session

    result = run_synthetic_session(max_turns=2, seed=51, use_fake_gm=True)
    assert isinstance(result, SyntheticRunResult)
    assert result.profile_name == "placeholder"
    assert result.stop_reason == "max_turns_reached"
    assert len(result.turn_views) == 2
    assert all(str(view.get("player_text", "")).strip() for view in result.turn_views)


def test_synthetic_scenario_presets_are_unique_and_fake_gm_runnable():
    """Guard stable scenario ids and that ``run_kwargs`` matches the runner surface."""
    from dataclasses import replace

    from tests.helpers.synthetic_runner import run_synthetic_session
    from tests.helpers.synthetic_scenarios import PRESET_FACTORIES, SyntheticScenario

    seen: set[str] = set()
    for factory in PRESET_FACTORIES:
        base = factory()
        assert isinstance(base, SyntheticScenario)
        assert base.scenario_id
        assert base.scenario_id not in seen
        seen.add(base.scenario_id)

        one_turn = replace(base, max_turns=1)
        kw = one_turn.run_kwargs(use_fake_gm=True)
        assert set(kw.keys()) == {"profile", "seed", "max_turns", "player_texts", "use_fake_gm"}
        result = run_synthetic_session(**kw)
        assert result.profile_name == one_turn.profile_factory().profile_id
        assert len(result.turn_views) == 1
