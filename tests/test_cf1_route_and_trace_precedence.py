"""CF1 — table-driven contracts for route-kind and trace-source projection precedence."""
from __future__ import annotations

import pytest

from tests.helpers.golden_replay_projection_extractors import (
    _resolve_route_kind,
    _trace_from_payload_or_snapshot,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "trace,resolution_compact,resolution,expected",
    [
        pytest.param(
            {"route_selected": "social"},
            {"kind": "compact_kind"},
            {"kind": "resolution_kind"},
            "social",
            id="trace_route_selected_wins",
        ),
        pytest.param(
            {},
            {"kind": "compact_kind"},
            {"kind": "resolution_kind"},
            "compact_kind",
            id="resolution_compact_when_trace_absent",
        ),
        pytest.param(
            {},
            None,
            {"kind": "resolution_kind"},
            "resolution_kind",
            id="resolution_kind_last_resort",
        ),
        pytest.param({}, None, {}, None, id="all_sources_absent"),
        pytest.param(
            {"route_selected": None},
            {"kind": "compact_kind"},
            {"kind": "resolution_kind"},
            "compact_kind",
            id="trace_null_falls_through_to_compact",
        ),
        pytest.param(
            {"route_selected": "trace_wins"},
            {"kind": "compact_loser"},
            {"kind": "resolution_loser"},
            "trace_wins",
            id="conflicting_trace_beats_compact_and_resolution",
        ),
    ],
)
def test_resolve_route_kind_precedence_matrix(
    trace: dict[str, object],
    resolution_compact: dict[str, object] | None,
    resolution: dict[str, object],
    expected: str | None,
) -> None:
    assert (
        _resolve_route_kind(
            social_contract_trace=trace,
            resolution_compact=resolution_compact,
            resolution=resolution,
        )
        == expected
    )


@pytest.mark.parametrize(
    "payload,snap,expected_turn_id",
    [
        pytest.param(
            {"debug_traces": [{"turn_id": "payload_trace", "compact": True}]},
            {"debug": {"last_debug_trace": {"turn_id": "snap_trace"}}},
            "payload_trace",
            id="payload_debug_traces_beats_snapshot",
        ),
        pytest.param(
            {"session": {"debug_traces": [{"turn_id": "session_trace", "compact": True}]}},
            {"debug": {"last_debug_trace": {"turn_id": "snap_trace"}}},
            "session_trace",
            id="session_nested_debug_traces_second",
        ),
        pytest.param(
            {},
            {"debug": {"last_debug_trace": {"turn_id": "snap_only"}}},
            "snap_only",
            id="snapshot_last_debug_trace_fallback",
        ),
        pytest.param({}, {}, None, id="empty_when_all_absent"),
    ],
)
def test_trace_from_payload_or_snapshot_precedence_matrix(
    payload: dict[str, object],
    snap: dict[str, object],
    expected_turn_id: str | None,
) -> None:
    trace = _trace_from_payload_or_snapshot(payload, snap)
    if expected_turn_id is None:
        assert trace == {}
    else:
        assert trace.get("turn_id") == expected_turn_id
