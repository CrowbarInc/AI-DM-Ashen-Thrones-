"""Lead inspection metadata under lead[\"metadata\"] (engine observability; deterministic)."""

from __future__ import annotations

import copy

import pytest

from game.leads import (
    SESSION_LEAD_REGISTRY_KEY,
    LeadLifecycle,
    LeadStatus,
    LeadType,
    _clear_last_progression_effects,
    _set_last_progression_effects,
    build_lead_debug_snapshot,
    create_lead,
    debug_dump_leads,
    diff_lead_debug_snapshots,
    format_lead_debug_delta,
    normalize_lead,
    reconcile_session_lead_progression,
    resolve_lead,
    set_lead_status,
    upsert_lead,
)

pytestmark = pytest.mark.unit


def test_normalize_lead_metadata_is_always_shallow_dict_copy():
    raw = {"id": "x", "title": "X", "metadata": {"a": 1, "b": {"nested": True}}}
    nested_before = raw["metadata"]["b"]
    normalize_lead(raw)
    assert isinstance(raw["metadata"], dict)
    assert raw["metadata"]["a"] == 1
    # Shallow copy: nested mapping values are shared with the source metadata.
    assert raw["metadata"]["b"] is nested_before
    raw["metadata"]["b"]["nested"] = False
    assert nested_before["nested"] is False

    raw2: dict = {"id": "y", "title": "Y", "metadata": None}
    normalize_lead(raw2)
    assert raw2["metadata"] == {}

    raw3: dict = {"id": "z", "title": "Z", "metadata": "bad"}
    normalize_lead(raw3)
    assert raw3["metadata"] == {}


def test_lifecycle_status_mutation_records_transition_metadata():
    lead = create_lead(title="T", summary="", id="t", lifecycle=LeadLifecycle.HINTED)
    set_lead_status(lead, LeadStatus.PURSUED, turn=3)
    meta = lead["metadata"]
    assert meta["last_transition_reason"] == "status_update"
    assert meta["last_transition_category"] == "status_change"
    assert meta["last_transition_turn"] == 3
    assert meta["last_transition_from_lifecycle"] == LeadLifecycle.HINTED.value
    assert meta["last_transition_to_lifecycle"] == LeadLifecycle.HINTED.value
    assert meta["last_transition_from_status"] == LeadStatus.ACTIVE.value
    assert meta["last_transition_to_status"] == LeadStatus.PURSUED.value


def test_idempotent_status_set_does_not_rewrite_transition_metadata():
    lead = create_lead(title="T", summary="", id="t")
    set_lead_status(lead, LeadStatus.PURSUED, turn=1)
    first = copy.deepcopy(lead["metadata"])
    set_lead_status(lead, LeadStatus.PURSUED, turn=99)
    assert lead["metadata"] == first


def test_idempotent_resolve_does_not_rewrite_transition_metadata():
    base = create_lead(
        title="R",
        summary="",
        id="r",
        lifecycle=LeadLifecycle.COMMITTED,
        status=LeadStatus.ACTIVE,
    )
    resolve_lead(base, resolution_type="climax", turn=5)
    meta_after_first = copy.deepcopy(base["metadata"])
    resolve_lead(base, resolution_type="climax", turn=99)
    assert base["metadata"] == meta_after_first


def test_reconcile_idempotent_no_progression_churn_on_second_pass():
    threat = create_lead(
        title="Th",
        summary="",
        id="th",
        type=LeadType.THREAT,
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.ACTIVE,
        first_discovered_turn=0,
    )
    session = {"turn_counter": 5, SESSION_LEAD_REGISTRY_KEY: {"th": threat}}
    reconcile_session_lead_progression(session, turn=5)
    meta1 = copy.deepcopy(session[SESSION_LEAD_REGISTRY_KEY]["th"]["metadata"])
    reconcile_session_lead_progression(session, turn=5)
    meta2 = session[SESSION_LEAD_REGISTRY_KEY]["th"]["metadata"]
    assert meta1 == meta2


def test_progression_effects_sorted_unique_and_bounded_merge():
    lead = create_lead(title="P", summary="", id="p")
    _set_last_progression_effects(lead, ["zeta", "alpha", "alpha"])
    assert lead["metadata"]["last_progression_effects"] == ["alpha", "zeta"]
    _set_last_progression_effects(lead, ["beta"])
    assert lead["metadata"]["last_progression_effects"] == ["alpha", "beta", "zeta"]
    _clear_last_progression_effects(lead)
    assert lead["metadata"]["last_progression_effects"] == []
    _clear_last_progression_effects(lead)
    assert lead["metadata"]["last_progression_effects"] == []


def test_inspection_metadata_survives_upsert_normalize_round_trip():
    row = create_lead(title="U", summary="", id="u")
    set_lead_status(row, LeadStatus.STALE, turn=2, transition_reason="stale_decay", transition_category="status_change")
    session: dict = {SESSION_LEAD_REGISTRY_KEY: {}}
    upsert_lead(session, row)
    stored = session[SESSION_LEAD_REGISTRY_KEY]["u"]
    round_trip = normalize_lead(dict(stored))
    assert round_trip["metadata"]["last_transition_reason"] == "stale_decay"
    assert round_trip["metadata"]["last_transition_to_status"] == LeadStatus.STALE.value


def test_debug_dump_leads_includes_inspection_and_core_fields():
    lead = create_lead(title="T1", summary="", id="z1", lifecycle=LeadLifecycle.HINTED)
    set_lead_status(lead, LeadStatus.PURSUED, turn=4)
    _set_last_progression_effects(lead, ["gamma", "alpha"])
    session = {SESSION_LEAD_REGISTRY_KEY: {"z1": lead}}
    rows = debug_dump_leads(session)
    assert len(rows) == 1
    r = rows[0]
    assert r["id"] == "z1"
    assert r["title"] == "T1"
    assert r["lifecycle"] == LeadLifecycle.HINTED.value
    assert r["status"] == LeadStatus.PURSUED.value
    assert r["priority"] == "0"
    assert r["last_updated_turn"] == "4"
    assert r["last_touched_turn"] == "4"
    assert r["superseded_by"] == ""
    assert r["obsolete_reason"] == ""
    assert r["resolution_type"] == ""
    assert r["last_transition_reason"] == "status_update"
    assert r["last_transition_category"] == "status_change"
    assert r["last_transition_turn"] == "4"
    assert r["last_transition_from_lifecycle"] == LeadLifecycle.HINTED.value
    assert r["last_transition_to_lifecycle"] == LeadLifecycle.HINTED.value
    assert r["last_transition_from_status"] == LeadStatus.ACTIVE.value
    assert r["last_transition_to_status"] == LeadStatus.PURSUED.value
    assert r["last_progression_effects"] == ["alpha", "gamma"]
    assert "type" in r and "confidence" in r
    assert r["resolved_at_turn"] == ""
    assert r["consequence_ids"] == ""


def test_debug_dump_leads_sorted_by_id_then_storage_key():
    session = {
        SESSION_LEAD_REGISTRY_KEY: {
            "b": create_lead(title="B", summary="", id="b"),
            "a": create_lead(title="A", summary="", id="a"),
        }
    }
    assert [r["id"] for r in debug_dump_leads(session)] == ["a", "b"]


def test_build_lead_debug_snapshot_is_deterministic_and_read_only():
    lead = create_lead(title="S", summary="", id="s")
    session: dict = {SESSION_LEAD_REGISTRY_KEY: {"s": lead}}
    snap_before = copy.deepcopy(session)
    s1 = build_lead_debug_snapshot(session)
    s2 = build_lead_debug_snapshot(session)
    assert session == snap_before
    assert s1 == s2
    assert list(s1.keys()) == ["s"]
    assert s1["s"]["id"] == "s"
    assert s1["s"]["title"] == "S"


def test_diff_lead_debug_snapshots_empty_for_identical():
    a = build_lead_debug_snapshot({SESSION_LEAD_REGISTRY_KEY: {"x": create_lead(title="X", summary="", id="x")}})
    assert diff_lead_debug_snapshots(a, dict(a)) == []


def test_diff_lead_debug_snapshots_changed_only_lists_differing_fields():
    b = build_lead_debug_snapshot({SESSION_LEAD_REGISTRY_KEY: {"x": create_lead(title="Old", summary="", id="x")}})
    session2 = {SESSION_LEAD_REGISTRY_KEY: {"x": create_lead(title="New", summary="", id="x")}}
    a = build_lead_debug_snapshot(session2)
    d = diff_lead_debug_snapshots(b, a)
    assert len(d) == 1
    assert d[0]["id"] == "x"
    assert d[0]["change_kind"] == "changed"
    assert d[0]["changed_fields"] == ["title"]
    assert d[0]["before"] == {"title": "Old"}
    assert d[0]["after"] == {"title": "New"}


def test_diff_lead_debug_snapshots_added_removed():
    b = build_lead_debug_snapshot({SESSION_LEAD_REGISTRY_KEY: {"only": create_lead(title="O", summary="", id="only")}})
    a = build_lead_debug_snapshot(
        {SESSION_LEAD_REGISTRY_KEY: {"new": create_lead(title="N", summary="", id="new")}}
    )
    d = diff_lead_debug_snapshots(b, a)
    assert [x["change_kind"] for x in d] == ["added", "removed"]
    assert [x["id"] for x in d] == ["new", "only"]
    assert d[0]["after"]["id"] == "new" and d[0]["before"] == {}
    assert d[1]["before"]["id"] == "only" and d[1]["after"] == {}


def test_diff_lead_debug_snapshots_ordering_deterministic_multi_change():
    reg_b = {
        "c": create_lead(title="c0", summary="", id="c"),
        "a": create_lead(title="a0", summary="", id="a"),
    }
    reg_a = {
        "c": create_lead(title="c1", summary="", id="c"),
        "a": create_lead(title="a1", summary="", id="a"),
    }
    b = build_lead_debug_snapshot({SESSION_LEAD_REGISTRY_KEY: reg_b})
    a = build_lead_debug_snapshot({SESSION_LEAD_REGISTRY_KEY: reg_a})
    d = diff_lead_debug_snapshots(b, a)
    assert [x["id"] for x in d] == ["a", "c"]
    assert all(x["change_kind"] == "changed" for x in d)


def test_progression_effects_sorted_in_dump_and_snapshot():
    lead = create_lead(title="P", summary="", id="p")
    _set_last_progression_effects(lead, ["z", "a", "m"])
    session = {SESSION_LEAD_REGISTRY_KEY: {"p": lead}}
    row = debug_dump_leads(session)[0]
    assert row["last_progression_effects"] == ["a", "m", "z"]
    snap = build_lead_debug_snapshot(session)["p"]
    assert snap["last_progression_effects"] == ["a", "m", "z"]


def test_debug_helpers_do_not_mutate_session():
    lead = create_lead(title="M", summary="", id="m")
    session: dict = {SESSION_LEAD_REGISTRY_KEY: {"m": lead}}
    frozen = copy.deepcopy(session)
    debug_dump_leads(session)
    build_lead_debug_snapshot(session)
    diff_lead_debug_snapshots(build_lead_debug_snapshot({}), build_lead_debug_snapshot(session))
    assert session == frozen


def test_format_lead_debug_delta_empty_for_no_op_diff():
    a = build_lead_debug_snapshot({SESSION_LEAD_REGISTRY_KEY: {"x": create_lead(title="X", summary="", id="x")}})
    assert format_lead_debug_delta(diff_lead_debug_snapshots(a, dict(a))) == []


def test_format_lead_debug_delta_added_removed_ordering():
    b = build_lead_debug_snapshot({SESSION_LEAD_REGISTRY_KEY: {"only": create_lead(title="O", summary="", id="only")}})
    a = build_lead_debug_snapshot({SESSION_LEAD_REGISTRY_KEY: {"new": create_lead(title="N", summary="", id="new")}})
    delta = diff_lead_debug_snapshots(b, a)
    assert format_lead_debug_delta(delta) == ["new added", "only removed"]


def test_format_lead_debug_delta_changed_order_follows_diff_rows():
    reg_b = {
        "c": create_lead(title="c0", summary="", id="c"),
        "a": create_lead(title="a0", summary="", id="a"),
    }
    reg_a = {
        "c": create_lead(title="c1", summary="", id="c"),
        "a": create_lead(title="a1", summary="", id="a"),
    }
    b = build_lead_debug_snapshot({SESSION_LEAD_REGISTRY_KEY: reg_b})
    a = build_lead_debug_snapshot({SESSION_LEAD_REGISTRY_KEY: reg_a})
    delta = diff_lead_debug_snapshots(b, a)
    lines = format_lead_debug_delta(delta)
    assert [ln.split(maxsplit=1)[0] for ln in lines] == ["a", "c"]
    assert all(ln.endswith(" changed: title") for ln in lines)


def test_format_lead_debug_delta_reason_category_consistent():
    row = {
        "id": "lead_x",
        "change_kind": "changed",
        "changed_fields": ["status", "priority"],
        "before": {"status": "active", "priority": "1"},
        "after": {"status": "stale", "priority": "2"},
        "reason": "stale_decay",
        "category": "status_change",
    }
    assert format_lead_debug_delta([row]) == [
        "lead_x changed: status, priority reason=stale_decay category=status_change"
    ]


def test_format_lead_debug_delta_progression_compact_and_read_only():
    prog_before = ["zeta", "alpha", "zeta"]
    prog_after = ["beta", "alpha"]
    row_changed = {
        "id": "p",
        "change_kind": "changed",
        "changed_fields": ["last_progression_effects"],
        "before": {"last_progression_effects": prog_before},
        "after": {"last_progression_effects": prog_after},
        "reason": "",
        "category": "",
    }
    row_added = {
        "id": "q",
        "change_kind": "added",
        "changed_fields": ["id"],
        "before": {},
        "after": {"id": "q", "last_progression_effects": ["gamma", "delta"]},
        "reason": "unlock_trigger",
        "category": "",
    }
    row_removed = {
        "id": "r",
        "change_kind": "removed",
        "changed_fields": ["id"],
        "before": {"id": "r", "last_progression_effects": ["omega"]},
        "after": {},
        "reason": "superseded",
        "category": "lifecycle_change",
    }
    delta = [row_changed, row_added, row_removed]
    frozen = copy.deepcopy(delta)
    prog_b_id = id(prog_before)
    prog_a_id = id(prog_after)

    lines = format_lead_debug_delta(delta)

    assert lines == [
        "p changed: last_progression_effects before=zeta,alpha,zeta after=beta,alpha",
        "q added reason=unlock_trigger last_progression_effects=gamma,delta",
        "r removed reason=superseded category=lifecycle_change last_progression_effects=omega",
    ]
    assert delta == frozen
    assert id(delta[0]["before"]["last_progression_effects"]) == prog_b_id
    assert id(delta[0]["after"]["last_progression_effects"]) == prog_a_id
    assert delta[0]["before"]["last_progression_effects"] == ["zeta", "alpha", "zeta"]
