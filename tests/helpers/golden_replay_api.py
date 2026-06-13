"""Narrow public API for golden replay harness consumers.

The implementation still lives in ``tests.helpers.golden_replay``. This facade
keeps downstream tests and report helpers from importing the broad harness
module directly.

Export only replay orchestration, observation consumption, protected assertion
bridge diagnostics, and long-session profile consumption helpers. Subsystem
legality remains in the owner suites documented by ``tests.test_ownership_registry``.
"""
from __future__ import annotations

from typing import Any, Mapping

from tests.helpers.golden_replay import (
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    _observed_turn,
    assert_fallback_escalation_profile,
    assert_golden_replay_profile_bundle,
    assert_golden_turn_observation,
    assert_long_session_stability_profile,
    assert_protected_golden_turn_observation,
    assert_runtime_lineage_event_matches,
    assert_runtime_lineage_profile,
    build_long_session_stability_scorecard,
    classify_golden_drift,
    compare_golden_replay_reruns,
    expected_runtime_fallback_lineage_event,
    format_golden_replay_debug,
    protected_social_speaker_observation_expectation,
    protected_structural_expectation,
    render_golden_replay_markdown_report,
    render_long_session_replay_summary_markdown,
    run_golden_replay,
    summarize_fallback_escalation_observations,
    summarize_long_session_replay_observations,
    summarize_response_delta_observations,
)


def observed_turn_from_payload(
    *,
    scenario_id: str,
    snap: dict[str, Any],
    payload: dict[str, Any],
    replay_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project one replay turn payload through the public golden replay API."""
    return _observed_turn(
        scenario_id=scenario_id,
        snap=snap,
        payload=payload,
        replay_identity=replay_identity,
    )


__all__ = (
    "NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY",
    "assert_fallback_escalation_profile",
    "assert_golden_replay_profile_bundle",
    "assert_golden_turn_observation",
    "assert_long_session_stability_profile",
    "assert_protected_golden_turn_observation",
    "assert_runtime_lineage_event_matches",
    "assert_runtime_lineage_profile",
    "build_long_session_stability_scorecard",
    "classify_golden_drift",
    "compare_golden_replay_reruns",
    "expected_runtime_fallback_lineage_event",
    "format_golden_replay_debug",
    "observed_turn_from_payload",
    "protected_social_speaker_observation_expectation",
    "protected_structural_expectation",
    "render_golden_replay_markdown_report",
    "render_long_session_replay_summary_markdown",
    "run_golden_replay",
    "summarize_fallback_escalation_observations",
    "summarize_long_session_replay_observations",
    "summarize_response_delta_observations",
)
