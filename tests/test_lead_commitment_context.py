"""commit_session_lead_with_context: explicit player commitment metadata and lifecycle wiring."""

from __future__ import annotations

from game.leads import (
    LeadLifecycle,
    LeadStatus,
    commit_session_lead_with_context,
    create_lead,
    get_lead,
    upsert_lead,
)


import pytest

pytestmark = pytest.mark.unit

def test_commit_discovered_lead_sets_committed_pursued_and_first_turn_stamp():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="Track",
            summary="",
            id="L1",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    out = commit_session_lead_with_context(
        session,
        "L1",
        turn=4,
        commitment_source="affordance",
        commitment_strength=2,
        next_step="Visit the warehouse",
    )
    row = get_lead(session, "L1")
    assert out is row
    assert row["lifecycle"] == "committed"
    assert row["status"] == "pursued"
    assert row["committed_at_turn"] == 4
    assert row["commitment_source"] == "affordance"
    assert row["commitment_strength"] == 2
    assert row["next_step"] == "Visit the warehouse"
    assert row["last_updated_turn"] == 4
    assert row["last_touched_turn"] == 4


def test_repeat_commit_preserves_committed_at_turn_updates_context():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="R",
            summary="",
            id="L2",
            lifecycle=LeadLifecycle.DISCOVERED,
        ),
    )
    commit_session_lead_with_context(
        session,
        "L2",
        turn=1,
        commitment_source="first",
        commitment_strength=1,
    )
    commit_session_lead_with_context(
        session,
        "L2",
        turn=9,
        commitment_source="second",
        commitment_strength=5,
        next_step="Follow the courier",
    )
    row = get_lead(session, "L2")
    assert row["committed_at_turn"] == 1
    assert row["commitment_source"] == "second"
    assert row["commitment_strength"] == 5
    assert row["next_step"] == "Follow the courier"
    assert row["last_updated_turn"] == 9


def test_repeat_commit_omitted_kwargs_leave_prior_commitment_metadata():
    session: dict = {}
    upsert_lead(session, create_lead(title="K", summary="", id="L3", lifecycle=LeadLifecycle.DISCOVERED))
    commit_session_lead_with_context(
        session,
        "L3",
        turn=1,
        commitment_source="keep-me",
        commitment_strength=7,
    )
    commit_session_lead_with_context(session, "L3", turn=2, next_step="Only step")
    row = get_lead(session, "L3")
    assert row["commitment_source"] == "keep-me"
    assert row["commitment_strength"] == 7
    assert row["next_step"] == "Only step"


def test_stale_discovered_lead_becomes_pursued_via_helper():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="Stale",
            summary="",
            id="L4",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.STALE,
        ),
    )
    commit_session_lead_with_context(session, "L4", turn=3)
    row = get_lead(session, "L4")
    assert row["lifecycle"] == "committed"
    assert row["status"] == "pursued"


def test_missing_lead_id_returns_none_without_registry_side_effects():
    session: dict = {}
    upsert_lead(session, create_lead(title="Only", summary="", id="only"))
    assert commit_session_lead_with_context(session, "nope", turn=1) is None
    assert get_lead(session, "nope") is None
    assert set(session.get("lead_registry", {}).keys()) == {"only"}


def test_resolved_lead_not_forced_into_illegal_state():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="Done",
            summary="",
            id="L5",
            lifecycle=LeadLifecycle.RESOLVED,
            status=LeadStatus.RESOLVED,
            resolved_at_turn=10,
        ),
    )
    before = dict(get_lead(session, "L5") or {})
    out = commit_session_lead_with_context(
        session,
        "L5",
        turn=99,
        commitment_source="should-not-apply",
        commitment_strength=9,
        next_step="nope",
    )
    row = get_lead(session, "L5")
    assert out is row
    assert row["lifecycle"] == "resolved"
    assert row["status"] == "resolved"
    assert row.get("commitment_source") is before.get("commitment_source")
    assert row.get("commitment_strength") is before.get("commitment_strength")
    assert row.get("next_step") == before.get("next_step")


def test_obsolete_lead_not_forced_into_illegal_state():
    session: dict = {}
    upsert_lead(
        session,
        create_lead(
            title="Old",
            summary="",
            id="L6",
            lifecycle=LeadLifecycle.OBSOLETE,
            status=LeadStatus.ACTIVE,
        ),
    )
    before = dict(get_lead(session, "L6") or {})
    out = commit_session_lead_with_context(session, "L6", turn=5, commitment_source="x")
    row = get_lead(session, "L6")
    assert out is row
    assert row["lifecycle"] == "obsolete"
    assert row["status"] == "active"
    assert row.get("commitment_source") is before.get("commitment_source")
