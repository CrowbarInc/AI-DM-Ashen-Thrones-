"""Tests for :mod:`game.telemetry_vocab` (canonical observational vocabulary)."""

from __future__ import annotations

from game.telemetry_vocab import (
    TELEMETRY_ACTION_OBSERVED,
    TELEMETRY_ACTION_UNKNOWN,
    TELEMETRY_PHASE_UNKNOWN,
    TELEMETRY_SCOPE_UNKNOWN,
    build_telemetry_event,
    normalize_owner,
    normalize_reason_list,
    normalize_telemetry_action,
    normalize_telemetry_phase,
    normalize_telemetry_scope,
)


def test_normalize_phase_accepts_canonical_case_insensitive() -> None:
    assert normalize_telemetry_phase("GATE") == "gate"
    assert normalize_telemetry_phase("engine") == "engine"


def test_normalize_phase_invalid_coerces_to_unknown() -> None:
    assert normalize_telemetry_phase(None) == TELEMETRY_PHASE_UNKNOWN
    assert normalize_telemetry_phase("") == TELEMETRY_PHASE_UNKNOWN
    assert normalize_telemetry_phase("not-a-phase") == TELEMETRY_PHASE_UNKNOWN
    assert normalize_telemetry_phase(42) == TELEMETRY_PHASE_UNKNOWN


def test_normalize_action_and_scope_unknown_fallback() -> None:
    assert normalize_telemetry_action("nope") == TELEMETRY_ACTION_UNKNOWN
    assert normalize_telemetry_scope({}) == TELEMETRY_SCOPE_UNKNOWN


def test_normalize_telemetry_action_verb_aliases_map_to_canonical() -> None:
    assert normalize_telemetry_action("observe") == TELEMETRY_ACTION_OBSERVED
    assert normalize_telemetry_action("OBSERVING") == TELEMETRY_ACTION_OBSERVED
    assert normalize_telemetry_action("repair") == "repaired"


def test_normalize_reason_list_none_empty_stable_dedupe() -> None:
    assert normalize_reason_list(None) == []
    assert normalize_reason_list([]) == []
    assert normalize_reason_list(["b", "a", "b", "  "]) == ["b", "a"]


def test_normalize_reason_list_single_string() -> None:
    assert normalize_reason_list("  x  ") == ["x"]


def test_normalize_reason_list_rejects_mapping() -> None:
    assert normalize_reason_list({"a": 1}) == []


def test_normalize_owner_trims_or_none() -> None:
    assert normalize_owner("  owner  ") == "owner"
    assert normalize_owner("") is None
    assert normalize_owner("   ") is None
    assert normalize_owner(None) is None
    assert normalize_owner(99) is None


def test_build_telemetry_event_canonical_shape_and_reason_merge() -> None:
    ev = build_telemetry_event(
        phase="gate",
        owner=" test ",
        action="repair",
        reason="first",
        reasons=["second", "first"],
        scope="turn",
        data={"k": 1},
    )
    assert set(ev.keys()) == {"phase", "owner", "action", "reasons", "scope", "data"}
    assert ev["phase"] == "gate"
    assert ev["owner"] == "test"
    assert ev["action"] == "repaired"
    assert ev["reasons"] == ["first", "second"]
    assert ev["scope"] == "turn"
    assert ev["data"] == {"k": 1}


def test_build_telemetry_event_invalid_fields_coerced() -> None:
    ev = build_telemetry_event(phase="x", action="y", scope="z", data="not-a-mapping")
    assert ev["phase"] == TELEMETRY_PHASE_UNKNOWN
    assert ev["action"] == TELEMETRY_ACTION_UNKNOWN
    assert ev["scope"] == TELEMETRY_SCOPE_UNKNOWN
    assert ev["data"] == {}
    assert ev["reasons"] == []


def test_normalize_reason_list_does_not_mutate_input() -> None:
    seq = ["a", "b"]
    seq_id = id(seq)
    _ = normalize_reason_list(seq)
    assert id(seq) == seq_id
    assert seq == ["a", "b"]
