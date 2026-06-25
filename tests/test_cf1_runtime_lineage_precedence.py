"""CF1 — table-driven contracts for payload vs FEM-rebuilt runtime lineage precedence.

Locks ``_runtime_lineage_events_from_payload`` (acceptance golden replay authority).
"""
from __future__ import annotations

import pytest

from game.runtime_lineage_telemetry import make_runtime_lineage_event

from tests.helpers.golden_replay_projection_extractors import _runtime_lineage_events_from_payload

pytestmark = pytest.mark.unit


def _payload_event(**kwargs: object) -> dict[str, object]:
    return make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner="game.final_emission_gate",
        fallback_kind="scene_opening",
        gate_path="opening_fallback",
        **kwargs,
    )


def _fem_rebuildable() -> dict[str, object]:
    return {
        "final_route": "replaced",
        "opening_recovered_via_fallback": True,
        "fallback_family_used": "scene_opening",
        "final_emitted_source": "opening_deterministic_fallback",
    }


@pytest.mark.parametrize(
    "payload,fem,expected_kind,expected_count",
    [
        pytest.param(
            {"observability_bundle": {"fem_runtime_lineage_events": [_payload_event(source="stamped")]}},
            _fem_rebuildable(),
            "stamped",
            1,
            id="payload_stamped_beats_fem_rebuild",
        ),
        pytest.param(
            {"observability_bundle": {"fem_runtime_lineage_events": []}},
            _fem_rebuildable(),
            None,
            0,
            id="explicit_empty_payload_list_blocks_fem_rebuild",
        ),
        pytest.param({}, _fem_rebuildable(), "fallback_selected", None, id="fem_rebuild_when_payload_key_absent"),
        pytest.param({}, {}, None, 0, id="empty_when_no_payload_key_and_empty_fem"),
    ],
)
def test_runtime_lineage_events_from_payload_precedence_matrix(
    payload: dict[str, object],
    fem: dict[str, object],
    expected_kind: str | None,
    expected_count: int | None,
) -> None:
    events = _runtime_lineage_events_from_payload(payload, fem)
    if expected_count is not None:
        assert len(events) == expected_count
    if expected_kind is None and expected_count == 0:
        assert events == []
    elif expected_kind == "stamped":
        assert events[0].get("source") == "stamped"
    elif expected_kind == "fallback_selected":
        assert events
        assert events[0].get("event_kind") == "fallback_selected"
