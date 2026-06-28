"""CF1 — table-driven contracts for acceptance fallback-family projection precedence.

Locks ``project_replay_fallback_family_from_fem`` and ``_resolve_fallback_family``
(lineage bridge) without full turn assembly.
"""
from __future__ import annotations

import pytest

from game.final_emission_replay_projection import SEALED_REPLACEMENT_SUBKIND_OPENING
from game.runtime_lineage_telemetry import make_runtime_lineage_event

from tests.helpers.golden_replay_projection_fallbacks import (
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    _resolve_fallback_family,
    project_replay_fallback_family_from_fem,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "fem,expected",
    [
        pytest.param(
            {"fallback_family_used": "scene_opening", "realization_fallback_family": "upstream_prepared_emission"},
            "scene_opening",
            id="diegetic_wins_when_both_present",
        ),
        pytest.param(
            {"fallback_family_used": None, "realization_fallback_family": "upstream_prepared_emission"},
            "upstream_prepared_emission",
            id="realization_when_diegetic_null",
        ),
        pytest.param(
            {"realization_fallback_family": "scene_opening"},
            "scene_opening",
            id="realization_when_diegetic_absent",
        ),
        pytest.param({}, None, id="both_fields_absent"),
        pytest.param(
            {"fallback_family_used": None, "realization_fallback_family": None},
            None,
            id="both_fields_explicit_null",
        ),
        pytest.param(
            {"fallback_family_used": "", "realization_fallback_family": "scene_opening"},
            "",
            id="empty_string_diegetic_treated_as_present",
        ),
        pytest.param(
            {"fallback_family_used": "scene_opening", "realization_fallback_family": "conflicting"},
            "scene_opening",
            id="conflicting_diegetic_always_wins",
        ),
        pytest.param(
            {
                "final_emitted_source": NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
                "realization_fallback_family": "strict_social_deterministic_fallback",
                "fallback_kind": "neutral_speaker_grounding_bridge",
            },
            NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            id="bridge_emission_source_beats_generic_realization",
        ),
    ],
)
def test_project_replay_fallback_family_from_fem_precedence_matrix(
    fem: dict[str, object],
    expected: str | None,
) -> None:
    assert project_replay_fallback_family_from_fem(fem) == expected


def _sealed_fallback_selected_event() -> dict[str, object]:
    return make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner="game.final_emission_gate",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_OPENING,
        gate_path="opening_fallback",
    )


@pytest.mark.parametrize(
    "fem,lineage,expected",
    [
        pytest.param(
            {
                "final_route": "replaced",
                "final_emitted_source": NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            },
            [_sealed_fallback_selected_event()],
            NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            id="bridge_inferred_when_fem_family_absent_and_lineage_sealed",
        ),
        pytest.param(
            {
                "final_route": "replaced",
                "final_emitted_source": NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            },
            [],
            NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            id="bridge_from_emission_source_without_lineage",
        ),
        pytest.param(
            {
                "fallback_family_used": "scene_opening",
                "final_route": "replaced",
                "final_emitted_source": NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            },
            [_sealed_fallback_selected_event()],
            "scene_opening",
            id="fem_diegetic_beats_bridge_when_present",
        ),
        pytest.param(
            {
                "final_route": "accepted",
                "final_emitted_source": NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            },
            [_sealed_fallback_selected_event()],
            NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            id="bridge_from_emission_source_without_replaced_route",
        ),
    ],
)
def test_resolve_fallback_family_full_chain_precedence_matrix(
    fem: dict[str, object],
    lineage: list[dict[str, object]],
    expected: str | None,
) -> None:
    assert _resolve_fallback_family(fem, lineage) == expected
