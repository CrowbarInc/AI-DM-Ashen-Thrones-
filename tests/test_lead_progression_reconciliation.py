"""Deterministic lead progression reconciliation (stale decay, threat escalation, unlocks, supersession)."""

from __future__ import annotations

import copy

import pytest

from game.leads import (
    SESSION_LEAD_REGISTRY_KEY,
    LeadLifecycle,
    LeadStatus,
    LeadType,
    compute_threat_escalation_level,
    create_lead,
    effective_lead_pressure_score,
    lead_staleness_age,
    normalize_lead,
    reconcile_session_lead_progression,
    reconcile_single_lead_progression,
    refresh_lead_touch,
    resolve_lead,
    should_decay_lead_to_stale,
)

pytestmark = pytest.mark.unit


def _session(turn: int, leads: dict) -> dict:
    return {"turn_counter": turn, SESSION_LEAD_REGISTRY_KEY: leads}


def test_normalize_backfills_progression_scalars():
    raw: dict = {"id": "x", "title": "X"}
    normalize_lead(raw)
    assert raw.get("escalation_level") == 0
    assert raw.get("escalation_reason") is None
    assert raw.get("escalated_at_turn") is None
    assert raw.get("unlocked_by_lead_id") is None
    assert raw.get("obsolete_by_lead_id") is None


def test_stale_decay_active_and_pursued():
    active = create_lead(
        title="A",
        summary="",
        id="a",
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.ACTIVE,
        stale_after_turns=2,
        first_discovered_turn=0,
    )
    pursued = create_lead(
        title="P",
        summary="",
        id="p",
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.PURSUED,
        stale_after_turns=2,
        first_discovered_turn=0,
    )
    session = _session(2, {"a": active, "p": pursued})
    summary = reconcile_session_lead_progression(session, turn=2)
    assert set(summary["staled"]) == {"a", "p"}
    reg = session[SESSION_LEAD_REGISTRY_KEY]
    assert reg["a"]["status"] == LeadStatus.STALE.value
    assert reg["a"]["last_updated_turn"] == 2
    assert reg["p"]["status"] == LeadStatus.STALE.value


def test_no_decay_for_terminal_leads():
    resolved = resolve_lead(
        create_lead(
            title="R",
            summary="",
            id="r",
            lifecycle=LeadLifecycle.COMMITTED,
            stale_after_turns=1,
            first_discovered_turn=0,
        ),
        resolution_type="test",
        turn=1,
    )
    session = _session(5, {"r": resolved})
    summary = reconcile_session_lead_progression(session, turn=5)
    assert summary["staled"] == []
    assert session[SESSION_LEAD_REGISTRY_KEY]["r"]["status"] == LeadStatus.RESOLVED.value


def test_threat_escalation_tiers_by_unattended_age():
    def threat_at(ref: int, now: int) -> int:
        row = create_lead(
            title="T",
            summary="",
            id="t",
            type=LeadType.THREAT,
            first_discovered_turn=ref,
        )
        return compute_threat_escalation_level(row, now)

    assert threat_at(5, 5) == 0
    assert threat_at(5, 6) == 0
    assert threat_at(5, 7) == 1
    assert threat_at(5, 8) == 1
    assert threat_at(5, 9) == 2
    assert threat_at(5, 10) == 2
    assert threat_at(5, 11) == 3
    assert lead_staleness_age(7, create_lead(title="x", summary="", id="x", first_discovered_turn=5)) == 2


def test_escalation_drops_after_touch_refresh():
    row = create_lead(
        title="T",
        summary="",
        id="t",
        type=LeadType.THREAT,
        first_discovered_turn=0,
    )
    session = _session(5, {"t": row})
    reconcile_session_lead_progression(session, turn=5)
    stored = session[SESSION_LEAD_REGISTRY_KEY]["t"]
    assert stored["escalation_level"] == 2

    refresh_lead_touch(stored, turn=5)
    reconcile_session_lead_progression(session, turn=5)
    assert stored["escalation_level"] == 0
    assert stored.get("escalation_reason") is None
    assert stored.get("escalated_at_turn") is None


def test_resolved_lead_unlocks_hinted_to_discovered():
    src = resolve_lead(
        create_lead(title="S", summary="", id="src", unlocks=["tgt"]),
        resolution_type="done",
        turn=3,
    )
    tgt = create_lead(title="T", summary="", id="tgt", lifecycle=LeadLifecycle.HINTED)
    session = _session(4, {"src": src, "tgt": tgt})
    summary = reconcile_session_lead_progression(session, turn=4)
    assert summary["unlocked"] == [{"source_lead_id": "src", "target_lead_id": "tgt"}]
    out = session[SESSION_LEAD_REGISTRY_KEY]["tgt"]
    assert out["lifecycle"] == LeadLifecycle.DISCOVERED.value
    assert out["discovery_source"] == "unlocked_by:src"
    assert out["unlocked_by_lead_id"] == "src"
    assert out["first_discovered_turn"] == 4


def test_resolved_lead_reactivates_stale_unlocked_target():
    src = resolve_lead(
        create_lead(title="S", summary="", id="src", unlocks=["tgt"]),
        resolution_type="done",
        turn=1,
    )
    tgt = create_lead(
        title="T",
        summary="",
        id="tgt",
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.STALE,
        first_discovered_turn=0,
    )
    session = _session(2, {"src": src, "tgt": tgt})
    summary = reconcile_session_lead_progression(session, turn=2)
    assert summary["unlocked"] == [{"source_lead_id": "src", "target_lead_id": "tgt"}]
    assert session[SESSION_LEAD_REGISTRY_KEY]["tgt"]["status"] == LeadStatus.ACTIVE.value


def test_superseding_obsoletes_older_rumor_not_resolved():
    new_l = create_lead(title="New", summary="", id="newer", supersedes=["old_rumor"])
    old = create_lead(title="Old", summary="", id="old_rumor", superseded_by="newer")
    resolved = resolve_lead(
        create_lead(title="Done", summary="", id="done_rumor", superseded_by="newer"),
        resolution_type="confirmed",
        turn=1,
    )
    session = _session(3, {"newer": new_l, "old_rumor": old, "done_rumor": resolved})
    summary = reconcile_session_lead_progression(session, turn=3)
    ob = summary["obsoleted"]
    assert {"source_lead_id": "newer", "target_lead_id": "old_rumor"} in ob
    assert all(x["target_lead_id"] != "done_rumor" for x in ob)
    assert session[SESSION_LEAD_REGISTRY_KEY]["old_rumor"]["lifecycle"] == LeadLifecycle.OBSOLETE.value
    assert session[SESSION_LEAD_REGISTRY_KEY]["old_rumor"]["obsolete_reason"] == "superseded"
    assert session[SESSION_LEAD_REGISTRY_KEY]["done_rumor"]["lifecycle"] == LeadLifecycle.RESOLVED.value


def test_missing_unlock_and_supersede_targets_no_crash():
    src = resolve_lead(
        create_lead(title="S", summary="", id="src", unlocks=["missing", "also-missing"]),
        resolution_type="x",
        turn=1,
    )
    orphan = create_lead(title="O", summary="", id="orphan", superseded_by="no_such_lead")
    session = _session(2, {"src": src, "orphan": orphan})
    summary = reconcile_session_lead_progression(session, turn=2)
    assert summary["unlocked"] == []
    assert summary["obsoleted"] == []


def test_reconcile_idempotent_same_turn():
    active = create_lead(
        title="A",
        summary="",
        id="a",
        stale_after_turns=1,
        first_discovered_turn=0,
    )
    session = _session(2, {"a": active})
    s1 = reconcile_session_lead_progression(session, turn=2)
    s2 = reconcile_session_lead_progression(session, turn=2)
    assert s1["staled"] == ["a"]
    assert s2["staled"] == []
    assert s2["escalated"] == []
    assert s2["unlocked"] == []
    assert s2["obsoleted"] == []


def test_summary_reports_only_actual_escalation_changes():
    row = create_lead(
        title="T",
        summary="",
        id="t",
        type=LeadType.THREAT,
        first_discovered_turn=0,
    )
    session = _session(3, {"t": row})
    s1 = reconcile_session_lead_progression(session, turn=3)
    assert s1["escalated"] == [{"lead_id": "t", "from": 0, "to": 1}]
    s2 = reconcile_session_lead_progression(session, turn=3)
    assert s2["escalated"] == []


def test_should_decay_uses_reference_turn_priority():
    # last_touched_turn wins over last_updated_turn: ref=9, age=1, threshold 2 => no decay
    lead = create_lead(
        title="L",
        summary="",
        id="l",
        stale_after_turns=2,
        first_discovered_turn=0,
        last_updated_turn=5,
        last_touched_turn=9,
    )
    assert should_decay_lead_to_stale(lead, current_turn=10) is False
    # Without touch, last_updated_turn=9 is ref => age 1 >= threshold 1 => decay
    lead2 = create_lead(
        title="L2",
        summary="",
        id="l2",
        stale_after_turns=1,
        first_discovered_turn=0,
        last_updated_turn=9,
    )
    assert should_decay_lead_to_stale(lead2, current_turn=10) is True


def test_reconcile_single_lead_progression_returns_copy_and_codes():
    row = create_lead(
        title="A",
        summary="",
        id="a",
        stale_after_turns=1,
        first_discovered_turn=0,
    )
    orig = copy.deepcopy(row)
    out, codes = reconcile_single_lead_progression(row, {}, current_turn=2)
    assert row == orig
    assert "staled" in codes
    assert out["status"] == LeadStatus.STALE.value


def test_effective_lead_pressure_score_formula():
    base = create_lead(title="B", summary="", id="b", priority=1, escalation_level=2)
    assert effective_lead_pressure_score(base, 0) == 1 + 4
    pursued = create_lead(
        title="P", summary="", id="p", priority=0, status=LeadStatus.PURSUED, escalation_level=0
    )
    assert effective_lead_pressure_score(pursued, 0) == 2
    stale = create_lead(title="S", summary="", id="s", status=LeadStatus.STALE)
    assert effective_lead_pressure_score(stale, 0) == 1


def test_reconcile_idempotent_same_turn_after_unlock_and_supersession():
    """Second same-turn pass must not re-emit unlock / obsoletion / stale / escalation deltas."""
    parent = resolve_lead(
        create_lead(title="P", summary="", id="parent", unlocks=["child"]),
        resolution_type="done",
        turn=1,
    )
    child = create_lead(title="C", summary="", id="child", lifecycle=LeadLifecycle.HINTED)
    newer = create_lead(title="N", summary="", id="newer", supersedes=["old_r"])
    old_r = create_lead(
        title="O",
        summary="",
        id="old_r",
        lifecycle=LeadLifecycle.DISCOVERED,
        superseded_by="newer",
    )
    session = _session(5, {"parent": parent, "child": child, "newer": newer, "old_r": old_r})
    s1 = reconcile_session_lead_progression(session, turn=5)
    assert s1["unlocked"] == [{"source_lead_id": "parent", "target_lead_id": "child"}]
    assert {"source_lead_id": "newer", "target_lead_id": "old_r"} in s1["obsoleted"]
    s2 = reconcile_session_lead_progression(session, turn=5)
    assert s2["unlocked"] == []
    assert s2["obsoleted"] == []
    assert s2["staled"] == []
    assert s2["escalated"] == []


def test_multi_effect_single_reconcile_registry_and_summary():
    """One progression pass can stale, escalate a threat, unlock a hinted child, and obsolete a rumor."""
    parent = resolve_lead(
        create_lead(title="Src", summary="", id="src_unlock", unlocks=["child_u"]),
        resolution_type="confirmed",
        turn=1,
    )
    child_u = create_lead(title="Child", summary="", id="child_u", lifecycle=LeadLifecycle.HINTED)
    stale_me = create_lead(
        title="Stale me",
        summary="",
        id="stale_me",
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.ACTIVE,
        stale_after_turns=1,
        first_discovered_turn=0,
    )
    threat_e = create_lead(
        title="Threat",
        summary="",
        id="threat_e",
        type=LeadType.THREAT,
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.ACTIVE,
        first_discovered_turn=0,
    )
    newer = create_lead(title="Newer", summary="", id="newer_m", supersedes=["old_m"])
    old_m = create_lead(
        title="Old rumor",
        summary="",
        id="old_m",
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.ACTIVE,
        superseded_by="newer_m",
    )
    session = _session(
        10,
        {
            "src_unlock": parent,
            "child_u": child_u,
            "stale_me": stale_me,
            "threat_e": threat_e,
            "newer_m": newer,
            "old_m": old_m,
        },
    )
    summary = reconcile_session_lead_progression(session, turn=10)
    assert "stale_me" in summary["staled"]
    assert any(e.get("lead_id") == "threat_e" and e.get("to", 0) >= 2 for e in summary["escalated"])
    assert summary["unlocked"] == [{"source_lead_id": "src_unlock", "target_lead_id": "child_u"}]
    assert {"source_lead_id": "newer_m", "target_lead_id": "old_m"} in summary["obsoleted"]

    reg = session[SESSION_LEAD_REGISTRY_KEY]
    assert reg["stale_me"]["status"] == LeadStatus.STALE.value
    assert int(reg["threat_e"].get("escalation_level") or 0) >= 2
    assert reg["child_u"]["lifecycle"] == LeadLifecycle.DISCOVERED.value
    assert reg["child_u"]["unlocked_by_lead_id"] == "src_unlock"
    assert reg["old_m"]["lifecycle"] == LeadLifecycle.OBSOLETE.value


def test_missing_ref_targets_leave_other_leads_intact():
    """Bad unlock / supersede references must not corrupt unrelated registry rows."""
    src = resolve_lead(
        create_lead(title="S", summary="", id="src_bad", unlocks=["missing_tgt"]),
        resolution_type="x",
        turn=1,
    )
    orphan = create_lead(title="O", summary="", id="orphan", superseded_by="no_such")
    clean = create_lead(
        title="Clean",
        summary="",
        id="clean_z",
        lifecycle=LeadLifecycle.DISCOVERED,
        status=LeadStatus.ACTIVE,
        priority=3,
        last_updated_turn=5,
        first_discovered_turn=0,
    )
    expected = copy.deepcopy(clean)
    session = _session(3, {"src_bad": src, "orphan": orphan, "clean_z": clean})
    reconcile_session_lead_progression(session, turn=3)
    reg = session[SESSION_LEAD_REGISTRY_KEY]
    for key in ("id", "title", "status", "lifecycle", "priority", "last_updated_turn", "first_discovered_turn"):
        assert reg["clean_z"].get(key) == expected.get(key)
    assert reg["orphan"]["lifecycle"] != LeadLifecycle.OBSOLETE.value
