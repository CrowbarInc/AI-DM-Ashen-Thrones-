"""Focused tests for authoritative lead-local relation helpers in game.leads."""

from __future__ import annotations

import pytest

from game.leads import (
    _ensure_invariants_after_mutation,
    add_lead_relation,
    create_lead,
    ensure_lead_registry,
    get_lead,
    get_related_lead_ids,
    obsolete_session_lead,
    obsolete_superseded_lead,
    remove_lead_relation,
    replace_lead_relations,
    resolve_session_lead,
    upsert_lead,
)

pytestmark = pytest.mark.unit


def test_add_remove_supersedes_maintains_superseded_by_inverse():
    session: dict = {}
    upsert_lead(session, create_lead(title="Old", summary="", id="old"))
    upsert_lead(session, create_lead(title="New", summary="", id="new"))

    add_lead_relation(session, "new", "supersedes", "old", turn=2)
    assert get_lead(session, "old")["superseded_by"] == "new"
    assert get_related_lead_ids(session, "new", "supersedes") == ["old"]

    remove_lead_relation(session, "new", "supersedes", "old", turn=3)
    assert get_lead(session, "old").get("superseded_by") is None
    assert get_related_lead_ids(session, "new", "supersedes") == []


def test_add_remove_unlocks_dedupes_and_no_ops():
    session: dict = {}
    upsert_lead(session, create_lead(title="A", summary="", id="a"))
    upsert_lead(session, create_lead(title="B", summary="", id="b"))

    add_lead_relation(session, "a", "unlocks", "b", turn=1)
    assert get_lead(session, "a")["unlocks"] == ["b"]

    add_lead_relation(session, "a", "unlocks", "b", turn=9)
    assert get_lead(session, "a")["unlocks"] == ["b"]
    assert get_lead(session, "a")["last_updated_turn"] == 1

    remove_lead_relation(session, "a", "unlocks", "b", turn=4)
    assert get_lead(session, "a")["unlocks"] == []

    remove_lead_relation(session, "a", "unlocks", "b", turn=5)
    assert get_lead(session, "a")["unlocks"] == []
    assert get_lead(session, "a")["last_updated_turn"] == 4


def test_parent_lead_id_validates_target_and_forbids_self_parent():
    session: dict = {}
    upsert_lead(session, create_lead(title="Child", summary="", id="child"))
    upsert_lead(session, create_lead(title="Par", summary="", id="par"))

    with pytest.raises(ValueError, match="target lead does not exist"):
        add_lead_relation(session, "child", "parent_lead_id", "missing")

    with pytest.raises(ValueError, match="cannot relate to itself"):
        add_lead_relation(session, "child", "parent_lead_id", "child")

    add_lead_relation(session, "child", "parent_lead_id", "par", turn=1)
    assert get_related_lead_ids(session, "child", "parent_lead_id") == ["par"]


def test_related_buckets_normalize_and_dedupe_on_replace():
    session: dict = {}
    upsert_lead(session, create_lead(title="L", summary="", id="lead"))

    replace_lead_relations(
        session,
        "lead",
        "related_clue_ids",
        [" alpha ", "alpha", 99, None, True, {"bad": 1}],
        turn=1,
    )
    assert get_lead(session, "lead")["related_clue_ids"] == ["alpha", "99"]

    replace_lead_relations(session, "lead", "related_npc_ids", ("n1", "n1", " n2 "), turn=2)
    assert get_lead(session, "lead")["related_npc_ids"] == ["n1", "n2"]

    replace_lead_relations(session, "lead", "related_location_ids", ["loc"], turn=3)
    assert get_lead(session, "lead")["related_location_ids"] == ["loc"]


def test_remove_absent_relationship_is_no_op_without_error():
    session: dict = {}
    upsert_lead(session, create_lead(title="A", summary="", id="a"))
    remove_lead_relation(session, "a", "blocked_by", "ghost")
    assert get_lead(session, "a")["blocked_by"] == []


def test_no_op_mutations_do_not_advance_turn_metadata():
    session: dict = {}
    a = create_lead(
        title="A",
        summary="",
        id="a",
        last_updated_turn=10,
        last_touched_turn=10,
    )
    b = create_lead(title="B", summary="", id="b", last_updated_turn=1, last_touched_turn=1)
    upsert_lead(session, a)
    upsert_lead(session, b)

    add_lead_relation(session, "a", "unlocks", "b", turn=99)
    assert get_lead(session, "a")["last_updated_turn"] == 99

    add_lead_relation(session, "a", "unlocks", "b", turn=200)
    assert get_lead(session, "a")["last_updated_turn"] == 99
    assert get_lead(session, "a")["last_touched_turn"] == 99

    remove_lead_relation(session, "a", "unlocks", "missing", turn=300)
    assert get_lead(session, "a")["last_updated_turn"] == 99

    replace_lead_relations(session, "a", "unlocks", ["b"], turn=400)
    assert get_lead(session, "a")["last_updated_turn"] == 99


def test_replace_supersedes_syncs_inverse_for_removed_targets():
    session: dict = {}
    upsert_lead(session, create_lead(title="A", summary="", id="a"))
    upsert_lead(session, create_lead(title="B", summary="", id="b"))
    upsert_lead(session, create_lead(title="C", summary="", id="c"))

    replace_lead_relations(session, "a", "supersedes", ["b", "c"], turn=1)
    assert get_lead(session, "b")["superseded_by"] == "a"
    assert get_lead(session, "c")["superseded_by"] == "a"

    replace_lead_relations(session, "a", "supersedes", ["c"], turn=2)
    assert get_lead(session, "b").get("superseded_by") is None
    assert get_lead(session, "c")["superseded_by"] == "a"


def test_missing_source_lead_raises():
    session: dict = {}
    with pytest.raises(ValueError, match="lead does not exist"):
        add_lead_relation(session, "nope", "unlocks", "x")


def test_supersedes_cycle_second_add_rejected():
    session: dict = {}
    upsert_lead(session, create_lead(title="A", summary="", id="a"))
    upsert_lead(session, create_lead(title="B", summary="", id="b"))
    add_lead_relation(session, "a", "supersedes", "b", turn=1)
    with pytest.raises(RuntimeError, match="supersedes_cycle"):
        add_lead_relation(session, "b", "supersedes", "a", turn=2)


def test_parent_cycle_second_assignment_rejected():
    session: dict = {}
    upsert_lead(session, create_lead(title="A", summary="", id="a"))
    upsert_lead(session, create_lead(title="B", summary="", id="b"))
    add_lead_relation(session, "a", "parent_lead_id", "b", turn=1)
    with pytest.raises(RuntimeError, match="parent_cycle"):
        add_lead_relation(session, "b", "parent_lead_id", "a", turn=2)


def test_inverse_supersedes_mismatch_rejected():
    session: dict = {}
    upsert_lead(session, create_lead(title="A", summary="", id="a"))
    upsert_lead(session, create_lead(title="B", summary="", id="b"))
    a = get_lead(session, "a")
    b = get_lead(session, "b")
    assert a is not None and b is not None
    a["supersedes"] = ["b"]
    b["superseded_by"] = None
    reg = ensure_lead_registry(session)
    with pytest.raises(RuntimeError, match="inverse_supersedes_mismatch"):
        _ensure_invariants_after_mutation(a, registry=reg)


def test_new_parent_rejected_when_parent_resolved():
    session: dict = {}
    upsert_lead(session, create_lead(title="Child", summary="", id="child"))
    upsert_lead(session, create_lead(title="Par", summary="", id="par"))
    resolve_session_lead(session, "par", turn=1, resolution_type="confirmed")
    with pytest.raises(ValueError, match="resolved or obsolete"):
        add_lead_relation(session, "child", "parent_lead_id", "par", turn=2)


def test_new_supersedes_rejected_when_source_obsolete():
    session: dict = {}
    upsert_lead(session, create_lead(title="A", summary="", id="a"))
    upsert_lead(session, create_lead(title="B", summary="", id="b"))
    obsolete_session_lead(session, "a", turn=1, obsolete_reason="superseded")
    with pytest.raises(ValueError, match="resolved or obsolete"):
        add_lead_relation(session, "a", "supersedes", "b", turn=2)


def test_obsolete_superseded_lead_rejects_conflicting_superseded_by():
    session: dict = {}
    upsert_lead(session, create_lead(title="Old", summary="", id="old"))
    upsert_lead(session, create_lead(title="A", summary="", id="a"))
    upsert_lead(session, create_lead(title="B", summary="", id="b"))
    add_lead_relation(session, "a", "supersedes", "old", turn=1)
    with pytest.raises(ValueError, match="incompatible"):
        obsolete_superseded_lead(session, "old", replaced_by_lead_id="b", turn=2)


def test_obsolete_superseded_lead_keeps_inverse_consistent_for_validator():
    session: dict = {}
    upsert_lead(session, create_lead(title="Old", summary="", id="old", lifecycle="discovered"))
    upsert_lead(session, create_lead(title="New", summary="", id="new", lifecycle="discovered"))
    obsolete_superseded_lead(session, "old", replaced_by_lead_id="new", turn=1)
    reg = ensure_lead_registry(session)
    new_row = get_lead(session, "new")
    assert new_row is not None
    _ensure_invariants_after_mutation(new_row, registry=reg)


def test_new_supersedes_rejected_when_source_resolved():
    session: dict = {}
    upsert_lead(session, create_lead(title="A", summary="", id="a"))
    upsert_lead(session, create_lead(title="B", summary="", id="b"))
    resolve_session_lead(session, "a", turn=1, resolution_type="confirmed")
    with pytest.raises(ValueError, match="resolved or obsolete"):
        add_lead_relation(session, "a", "supersedes", "b", turn=2)


def test_blocked_by_unlocks_reject_self_and_duplicates():
    session: dict = {}
    upsert_lead(session, create_lead(title="A", summary="", id="a"))
    upsert_lead(session, create_lead(title="B", summary="", id="b"))
    reg = ensure_lead_registry(session)
    a = get_lead(session, "a")
    assert a is not None
    a["blocked_by"] = ["a"]
    with pytest.raises(RuntimeError, match="relation_self_link"):
        _ensure_invariants_after_mutation(a, registry=reg)
    a["blocked_by"] = ["b", "b"]
    with pytest.raises(RuntimeError, match="relation_duplicate_in_blocked_by"):
        _ensure_invariants_after_mutation(a, registry=reg)
    a["blocked_by"] = []
    a["unlocks"] = ["a"]
    with pytest.raises(RuntimeError, match="relation_self_link"):
        _ensure_invariants_after_mutation(a, registry=reg)
    a["unlocks"] = ["b", "b"]
    with pytest.raises(RuntimeError, match="relation_duplicate_in_unlocks"):
        _ensure_invariants_after_mutation(a, registry=reg)
