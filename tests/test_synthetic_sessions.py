"""Synthetic-player session harness under pytest (fake-GM by default).

Developer note: ``py -m pytest -q`` uses ``pytest.ini`` addopts ``-q`` only (no marker
deselection), so the default run **does** collect and execute synthetic-player tests:

- This module (``unit`` + ``synthetic``): runner wiring, ``run_synthetic_session``, presets.
- ``test_synthetic_policy.py`` (``unit`` + ``synthetic``): policy helpers.
- ``test_synthetic_smoke.py`` (``synthetic`` + ``slow``): heavier multi-turn smoke.

The **fast lane** ``-m "not transcript and not slow"`` skips ``test_synthetic_smoke.py``;
synthetic coverage still runs from this file and ``test_synthetic_policy.py``.

NPC / social **lead disclosure continuity** (same NPC + same lead advances ``mention_count``,
``npc_lead_discussions`` stays NPC-scoped) is not asserted by the fake-GM smoke lane, which only
checks policy template slugs and player-facing hygiene. Engine-level locks live in
``tests/test_social_lead_landing.py`` and ``tests/test_prompt_context.py``; the transcript-backed
``run_synthetic_session`` regression below anchors the harness to that persistence.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

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


def test_synthetic_player_session_fake_gm_returns_turn_views():
    """Regression anchor: real ``run_synthetic_session`` path with deterministic fake-GM."""
    from tests.helpers.synthetic_runner import run_synthetic_session

    result = run_synthetic_session(max_turns=2, seed=51, use_fake_gm=True)
    assert isinstance(result, SyntheticRunResult)
    assert result.profile_name == "placeholder"
    assert result.stop_reason == "max_turns_reached"
    assert len(result.turn_views) == 2
    assert all(str(view.get("player_text", "")).strip() for view in result.turn_views)


def test_synthetic_player_scenario_presets_are_unique_and_fake_gm_runnable():
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


def _gm_gate_opening() -> dict[str, Any]:
    return {
        "player_facing_text": (
            'The gate says, "Rain hammers the cobbles; torches hiss; the queue shuffles forward."'
        ),
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }


def _gm_captain_line(line: str) -> dict[str, Any]:
    return {
        "player_facing_text": f'The captain says, "{line}"',
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }


def _last_user_message_text(messages: list[dict[str, str]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return str(m.get("content") or "")
    return ""


@pytest.mark.integration
def test_synthetic_transcript_npc_lead_discussion_continuity_same_npc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``run_synthetic_session`` + real chat: same-NPC follow-up keeps interlocutor lead continuity.

    Deterministic GM via patched ``call_gpt``. A second Guard Captain line may not re-populate
    ``lead_landing`` (so ``apply_social_lead_discussion_tracking`` can no-op), but
    :func:`game.prompt_context.build_interlocutor_lead_discussion_context` must still surface
    **progress-over-restatement** for leads this NPC already introduced; this is the export hook
    that blocks treating recent leads like brand-new intros on immediate follow-ups. Also asserts
    NPC-scoped storage
    (no mirror row under ``tavern_runner`` for the same lead id).
    """
    from game.prompt_context import build_interlocutor_lead_discussion_context
    from game.social import get_npc_lead_discussion
    from game.storage import load_session

    from tests.helpers.synthetic_runner import run_synthetic_session

    def call_gpt(messages: list[dict[str, str]]) -> dict[str, Any]:
        last = _last_user_message_text(messages).strip()
        low = last.lower()
        if low.rstrip(".") == "begin" or last.startswith("Begin."):
            return _gm_gate_opening()
        # Next-step phrasing helps satisfy the NPC response contract when retries are enabled elsewhere.
        if "where" in low and "last sent" in low:
            return _gm_captain_line(
                "Follow the east road toward the old milestone; that is where the watch last sent the patrol."
            )
        if "milestone" in low or "east road" in low:
            return _gm_captain_line(
                "The milestone is the fork where the east road splits; ask there after dusk if you need names."
            )
        return _gm_captain_line("I have nothing more on that.")

    monkeypatch.setattr("game.api.call_gpt", call_gpt)
    # Lead-discussion tracking runs on the social resolution path; skip targeted GM retry loops here so
    # a stubbed ``call_gpt`` is not penalized for structured-fact / contract heuristics meant for real models.
    monkeypatch.setattr("game.api.detect_retry_failures", lambda **kwargs: [])

    # Second line must parse as a social ``question`` (engine path); vague follow-ups can fall through to
    # procedural GPT, which skips ``apply_social_lead_discussion_tracking``.
    texts = (
        "Begin.",
        "Guard Captain, where was the missing patrol last sent?",
        "Guard Captain, clarify what you meant about the east road and the old milestone.",
    )
    result = run_synthetic_session(
        max_turns=len(texts),
        seed=8801,
        use_fake_gm=False,
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        starting_scene_id="frontier_gate",
        player_texts=texts,
    )
    assert result.ok is True
    assert result.stop_reason == "max_turns_reached"
    assert len(result.turn_views) == len(texts)

    session = load_session()
    scene_id = "frontier_gate"

    ilc = build_interlocutor_lead_discussion_context(
        session=session,
        world={},
        public_scene={"id": scene_id},
        recent_log=[],
        active_npc_id="guard_captain",
    )
    assert ilc.get("active_npc_id") == "guard_captain"
    actionable = ilc.get("introduced_by_npc") if isinstance(ilc.get("introduced_by_npc"), list) else []
    assert actionable, f"expected>=1 actionable interlocutor lead row; got {ilc!r}"
    repeat = ilc.get("repeat_suppression") if isinstance(ilc.get("repeat_suppression"), dict) else {}
    assert repeat.get("prefer_progress_over_restatement") is True, (
        f"expected progress-over-restatement after same-NPC follow-up window; repeat={repeat!r}"
    )
    assert repeat.get("has_recent_repeat_risk") is True

    scene_state = session.get("scene_state") if isinstance(session.get("scene_state"), dict) else {}
    assert str(scene_state.get("current_interlocutor") or "").strip() == "guard_captain"

    lead_id = str(actionable[0].get("lead_id") or "").strip()
    assert lead_id
    assert get_npc_lead_discussion(session, scene_id, "tavern_runner", lead_id) is None
