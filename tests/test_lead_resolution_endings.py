"""Lead terminal endings: resolve / obsolete API, consequence_ids, and invariants."""

from __future__ import annotations

import copy

import pytest

from game.leads import (
    LeadLifecycle,
    LeadStatus,
    _collect_lead_invariant_violations,
    add_lead_relation,
    create_lead,
    debug_dump_leads,
    get_lead,
    get_related_lead_ids,
    is_lead_terminal,
    list_active_session_leads,
    list_session_leads,
    normalize_lead,
    obsolete_lead,
    obsolete_session_lead,
    obsolete_superseded_lead,
    resolve_lead,
    resolve_session_lead,
    upsert_lead,
)

pytestmark = pytest.mark.unit


def test_normalize_lead_consequence_ids_default_and_normalization():
    raw: dict = {"id": "c", "title": "C"}
    normalize_lead(raw)
    assert raw["consequence_ids"] == []

    raw2 = {
        "id": "d",
        "title": "D",
        "consequence_ids": ["  x  ", "y", "x", "", None, 99],
    }
    normalize_lead(raw2)
    assert raw2["consequence_ids"] == ["x", "y", "99"]


def test_create_lead_consequence_ids_normalized():
    lead = create_lead(
        title="T",
        summary="",
        id="lead-cq",
        consequence_ids=["a", "a", "b"],
    )
    assert lead["consequence_ids"] == ["a", "b"]


def test_resolve_lead_discovered_to_resolved_stamps_core_fields():
    lead = create_lead(
        title="R",
        summary="body",
        id="L1",
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.ACTIVE,
    )
    out = resolve_lead(
        lead,
        resolution_type="  Mystery Solved ",
        resolution_summary="  done  ",
        turn=7,
        consequence_ids=["fx-1", "fx-2"],
    )
    assert out["lifecycle"] == "resolved"
    assert out["status"] == "resolved"
    assert out["resolved_at_turn"] == 7
    assert out["resolution_type"] == "mystery solved"
    assert out["resolution_summary"] == "done"
    assert out["consequence_ids"] == ["fx-1", "fx-2"]
    assert out["last_updated_turn"] == 7


def test_resolve_lead_blank_summary_becomes_none():
    lead = create_lead(
        title="R2",
        summary="",
        id="L2",
        lifecycle=LeadLifecycle.DISCOVERED,
    )
    resolve_lead(lead, resolution_type="closed", resolution_summary="   ", turn=1)
    assert lead["resolution_summary"] is None


def test_obsolete_lead_committed_to_obsolete_stamps_reason_and_status():
    lead = create_lead(
        title="O",
        summary="",
        id="L3",
        lifecycle=LeadLifecycle.COMMITTED,
        status=LeadStatus.PURSUED,
    )
    out = obsolete_lead(lead, obsolete_reason="  Thread dropped  ", turn=3, consequence_ids=["c1"])
    assert out["lifecycle"] == "obsolete"
    assert out["status"] == "active"
    assert out["obsolete_reason"] == "Thread dropped"
    assert out["consequence_ids"] == ["c1"]
    assert out["last_updated_turn"] == 3


def test_resolve_lead_preserves_consequence_ids_when_omitted():
    lead = create_lead(
        title="P",
        summary="",
        id="L4",
        lifecycle=LeadLifecycle.DISCOVERED,
        consequence_ids=["keep-a", "keep-b"],
    )
    resolve_lead(lead, resolution_type="win", turn=1)
    assert lead["consequence_ids"] == ["keep-a", "keep-b"]


def test_resolve_lead_replaces_consequence_ids_when_provided():
    lead = create_lead(
        title="Q",
        summary="",
        id="L5",
        lifecycle=LeadLifecycle.DISCOVERED,
        consequence_ids=["old"],
    )
    resolve_lead(lead, resolution_type="win", turn=1, consequence_ids=["new"])
    assert lead["consequence_ids"] == ["new"]


def test_obsolete_lead_replaces_consequence_ids_when_provided():
    lead = create_lead(
        title="Q2",
        summary="",
        id="L6",
        lifecycle=LeadLifecycle.DISCOVERED,
        consequence_ids=["old"],
    )
    obsolete_lead(lead, obsolete_reason="nope", turn=1, consequence_ids=["n1", "n2"])
    assert lead["consequence_ids"] == ["n1", "n2"]


def test_resolve_lead_rejects_blank_resolution_type():
    lead = create_lead(title="X", summary="", id="L7", lifecycle=LeadLifecycle.DISCOVERED)
    with pytest.raises(ValueError, match="resolution_type"):
        resolve_lead(lead, resolution_type="  ")
    with pytest.raises(ValueError, match="resolution_type"):
        resolve_lead(lead, resolution_type="")


def test_obsolete_lead_rejects_blank_obsolete_reason():
    lead = create_lead(title="Y", summary="", id="L8", lifecycle=LeadLifecycle.DISCOVERED)
    with pytest.raises(ValueError, match="obsolete_reason"):
        obsolete_lead(lead, obsolete_reason="   ")
    with pytest.raises(ValueError, match="obsolete_reason"):
        obsolete_lead(lead, obsolete_reason="")


def test_resolve_already_resolved_same_payload_is_no_op():
    lead = create_lead(
        title="Z",
        summary="",
        id="L9",
        lifecycle=LeadLifecycle.RESOLVED,
        status=LeadStatus.RESOLVED,
        resolution_type="same",
        resolution_summary="sum",
    )
    lead["resolved_at_turn"] = 4
    lead["consequence_ids"] = ["a"]
    lead["last_updated_turn"] = 4
    before = copy.deepcopy(lead)
    resolve_lead(
        lead,
        resolution_type="same",
        resolution_summary="sum",
        turn=99,
        consequence_ids=["a"],
    )
    assert lead["resolved_at_turn"] == before["resolved_at_turn"]
    assert lead["last_updated_turn"] == before["last_updated_turn"]
    assert lead["resolution_type"] == "same"


def test_session_wrappers_mutate_registry_row():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="S",
            summary="",
            id="reg1",
            lifecycle=LeadLifecycle.DISCOVERED,
        ),
    )
    row = resolve_session_lead(
        session,
        "reg1",
        resolution_type="done",
        resolution_summary="ok",
        turn=2,
        consequence_ids=["fx"],
    )
    stored = get_lead(session, "reg1")
    assert row is stored
    assert stored["lifecycle"] == "resolved"
    assert stored["resolution_type"] == "done"
    assert stored["consequence_ids"] == ["fx"]

    upsert_lead(
        session,
        create_lead(title="S2", summary="", id="reg2", lifecycle=LeadLifecycle.DISCOVERED),
    )
    row2 = obsolete_session_lead(session, "reg2", obsolete_reason="gone", turn=5)
    assert row2 is get_lead(session, "reg2")
    assert row2["lifecycle"] == "obsolete"
    assert row2["obsolete_reason"] == "gone"


def test_session_wrappers_raise_when_lead_missing():
    session: dict = {}
    with pytest.raises(ValueError, match="lead_id"):
        resolve_session_lead(session, "", resolution_type="x")
    with pytest.raises(ValueError, match="does not exist"):
        resolve_session_lead(session, "nope", resolution_type="x")
    with pytest.raises(ValueError, match="lead_id"):
        obsolete_session_lead(session, None, obsolete_reason="x")
    with pytest.raises(ValueError, match="does not exist"):
        obsolete_session_lead(session, "missing", obsolete_reason="x")


def test_cannot_resolve_from_obsolete():
    lead = create_lead(
        title="T",
        summary="",
        id="L10",
        lifecycle=LeadLifecycle.OBSOLETE,
        status=LeadStatus.ACTIVE,
        obsolete_reason="old",
    )
    with pytest.raises(ValueError, match="obsolete"):
        resolve_lead(lead, resolution_type="try")


def test_cannot_go_backward_from_resolved_to_discovered_via_advance_not_this_api():
    """Terminal states: resolve_lead does not unwind obsolete; advance would reject backward."""
    from game.leads import advance_lead_lifecycle

    lead = create_lead(
        title="U",
        summary="",
        id="L11",
        lifecycle=LeadLifecycle.RESOLVED,
        status=LeadStatus.RESOLVED,
        resolution_type="r",
    )
    with pytest.raises(ValueError):
        advance_lead_lifecycle(lead, LeadLifecycle.DISCOVERED, turn=1)


def test_obsolete_default_keeps_resolution_fields_when_resolved_then_obsolete():
    lead = create_lead(
        title="V",
        summary="",
        id="L12",
        lifecycle=LeadLifecycle.RESOLVED,
        status=LeadStatus.RESOLVED,
        resolution_type="found",
        resolution_summary="details",
    )
    lead["resolved_at_turn"] = 2
    obsolete_lead(lead, obsolete_reason="no longer relevant", turn=8, clear_resolution_fields=False)
    assert lead["lifecycle"] == "obsolete"
    assert lead["resolution_type"] == "found"
    assert lead["resolution_summary"] == "details"
    assert lead["resolved_at_turn"] == 2


def test_obsolete_clear_resolution_fields_policy():
    lead = create_lead(
        title="W",
        summary="",
        id="L13",
        lifecycle=LeadLifecycle.RESOLVED,
        status=LeadStatus.RESOLVED,
        resolution_type="x",
    )
    lead["resolved_at_turn"] = 1
    obsolete_lead(lead, obsolete_reason="wipe", turn=3, clear_resolution_fields=True)
    assert lead["resolved_at_turn"] is None
    assert lead["resolution_type"] is None
    assert lead["resolution_summary"] is None


def test_invariants_still_hold_after_resolve_and_obsolete():
    lead = create_lead(title="Inv", summary="", id="L14", lifecycle=LeadLifecycle.DISCOVERED)
    resolve_lead(lead, resolution_type="ok", turn=1)
    assert _collect_lead_invariant_violations(lead) == []

    lead2 = create_lead(title="Inv2", summary="", id="L15", lifecycle=LeadLifecycle.DISCOVERED)
    obsolete_lead(lead2, obsolete_reason="reason", turn=1)
    assert _collect_lead_invariant_violations(lead2) == []


def test_resolve_clears_obsolete_reason_by_default():
    lead = create_lead(
        title="Clr",
        summary="",
        id="L16",
        lifecycle=LeadLifecycle.DISCOVERED,
    )
    lead["obsolete_reason"] = "stale"
    resolve_lead(lead, resolution_type="fixed", turn=1)
    assert lead["obsolete_reason"] is None


def test_resolve_clear_obsolete_reason_false_rejects_when_obsolete_reason_set():
    lead = create_lead(
        title="Str",
        summary="",
        id="L17",
        lifecycle=LeadLifecycle.DISCOVERED,
    )
    lead["obsolete_reason"] = "stray"
    with pytest.raises(ValueError, match="obsolete_reason"):
        resolve_lead(lead, resolution_type="t", turn=1, clear_obsolete_reason=False)


def test_is_lead_terminal_non_terminal_lifecycles():
    for lc, st in (
        (LeadLifecycle.DISCOVERED, LeadStatus.ACTIVE),
        (LeadLifecycle.COMMITTED, LeadStatus.PURSUED),
        (LeadLifecycle.HINTED, LeadStatus.ACTIVE),
    ):
        row = create_lead(title="T", summary="", id="x", lifecycle=lc, status=st)
        assert is_lead_terminal(row) is False


def test_is_lead_terminal_resolved_and_obsolete():
    r = create_lead(
        title="R",
        summary="",
        id="r1",
        lifecycle=LeadLifecycle.RESOLVED,
        status=LeadStatus.RESOLVED,
        resolution_type="done",
    )
    assert is_lead_terminal(r) is True
    o = create_lead(
        title="O",
        summary="",
        id="o1",
        lifecycle=LeadLifecycle.OBSOLETE,
        status=LeadStatus.ACTIVE,
        obsolete_reason="gone",
    )
    assert is_lead_terminal(o) is True


def test_list_active_and_list_session_exclude_terminal_sorted_by_id():
    session: dict = {}
    upsert_lead(session, create_lead(title="B", summary="", id="b", lifecycle=LeadLifecycle.DISCOVERED))
    upsert_lead(session, create_lead(title="A", summary="", id="a", lifecycle=LeadLifecycle.COMMITTED))
    upsert_lead(session, create_lead(title="Z", summary="", id="z", lifecycle=LeadLifecycle.DISCOVERED))
    resolve_session_lead(session, "z", resolution_type="closed", turn=1)
    upsert_lead(
        session,
        create_lead(title="O", summary="", id="o", lifecycle=LeadLifecycle.DISCOVERED),
    )
    obsolete_session_lead(session, "o", obsolete_reason="drop", turn=2)

    all_rows = list_session_leads(session, include_terminal=True)
    assert [r["id"] for r in all_rows] == ["a", "b", "o", "z"]

    active = list_active_session_leads(session)
    assert [r["id"] for r in active] == ["a", "b"]
    assert list_session_leads(session, include_terminal=False) == active

    mut = active[0]
    mut["title"] = "mutated"
    assert get_lead(session, mut["id"])["title"] != "mutated"


def test_debug_dump_leads_includes_compact_ending_metadata():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(title="L", summary="", id="ld", lifecycle=LeadLifecycle.DISCOVERED),
    )
    resolve_session_lead(
        session,
        "ld",
        resolution_type="Mystery Solved",
        resolution_summary="ok",
        turn=5,
        consequence_ids=["c1", "c2"],
    )
    rows = debug_dump_leads(session)
    assert len(rows) == 1
    row = rows[0]
    assert row["resolved_at_turn"] == "5"
    assert row["resolution_type"] == "mystery solved"
    assert row["obsolete_reason"] == ""
    assert row["consequence_ids"] == "c1,c2"

    obsolete_session_lead(session, "ld", obsolete_reason="redacted", turn=9)
    rows2 = debug_dump_leads(session)[0]
    assert rows2["lifecycle"] == "obsolete"
    assert rows2["obsolete_reason"] == "redacted"
    assert rows2["resolution_type"] == "mystery solved"


def test_obsolete_superseded_lead_sets_reason_and_optional_relation():
    session: dict = {}
    upsert_lead(session, create_lead(title="Old", summary="", id="old", lifecycle=LeadLifecycle.DISCOVERED))
    upsert_lead(session, create_lead(title="New", summary="", id="new", lifecycle=LeadLifecycle.DISCOVERED))
    out = obsolete_superseded_lead(session, "old", replaced_by_lead_id="new", turn=3, consequence_ids=["x"])
    assert out["lifecycle"] == "obsolete"
    assert out["obsolete_reason"] == "superseded"
    assert out["consequence_ids"] == ["x"]
    assert get_lead(session, "old")["superseded_by"] == "new"
    assert get_related_lead_ids(session, "new", "supersedes") == ["old"]


def test_obsolete_superseded_lead_idempotent_when_relation_already_present():
    session: dict = {}
    upsert_lead(session, create_lead(title="Old", summary="", id="old", lifecycle=LeadLifecycle.DISCOVERED))
    upsert_lead(session, create_lead(title="New", summary="", id="new", lifecycle=LeadLifecycle.DISCOVERED))
    add_lead_relation(session, "new", "supersedes", "old", turn=1)
    obsolete_superseded_lead(session, "old", replaced_by_lead_id="new", turn=2)
    assert get_lead(session, "old")["superseded_by"] == "new"
    assert get_lead(session, "old")["obsolete_reason"] == "superseded"
