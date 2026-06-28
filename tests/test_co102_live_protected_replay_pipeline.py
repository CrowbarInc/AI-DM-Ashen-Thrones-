"""CO102 live protected replay pipeline validation (opt-in).

Runs a genuine golden replay, records a protected assertion failure, and relies on
pytest sessionfinish to write committed recurrence artifacts.

Run:
  ASHEN_RUN_CO102_LIVE_VALIDATION=1 python -m pytest tests/test_co102_live_protected_replay_pipeline.py -q
"""
from __future__ import annotations

import os

import pytest

from tests.helpers.golden_replay import (
    assert_protected_golden_turn_observation,
    format_golden_replay_debug,
    protected_social_speaker_observation_expectation,
    run_golden_replay,
)
from tests.helpers.golden_replay_fixtures import (
    gm_response,
    golden_replay_chat_stubs,
    seed_runner_continuity_world,
)

pytestmark = [
    pytest.mark.golden_replay,
    pytest.mark.skipif(
        str(os.environ.get("ASHEN_RUN_CO102_LIVE_VALIDATION") or "").strip().lower()
        not in {"1", "true", "yes", "on"},
        reason=(
            "CO102 live validation is opt-in; set ASHEN_RUN_CO102_LIVE_VALIDATION=1 "
            "to exercise the protected replay observation pipeline end-to-end."
        ),
    ),
]


def test_co102_live_protected_replay_records_session_failure_artifacts(tmp_path, monkeypatch) -> None:
    """Execute golden replay then fail protected observation to populate session buffers."""
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response('Merchant says, "I know nothing about that."'),
    )

    result = run_golden_replay(
        scenario_id="wrong_speaker_strict_social_emission",
        turns=["Who attacked the patrol?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_runner_continuity_world,
    )

    turn = result["turns"][0]
    assert_protected_golden_turn_observation(
        turn,
        protected_social_speaker_observation_expectation("merchant"),
        scenario_id="wrong_speaker_strict_social_emission",
        debug_context=format_golden_replay_debug(result),
    )
