"""High-level contract tests for the lead lifecycle (discovery through prompt/journal alignment).

Run:
  pytest -q tests/test_lead_lifecycle_vertical_slice.py
  pytest -q tests/test_lead_lifecycle_vertical_slice.py -k "commitment or resolution or supersession or journal or prompt"
"""

from __future__ import annotations

import pytest

from game.clues import apply_authoritative_clue_discovery
from game.exploration import process_investigation_discovery
from game.journal import build_player_journal
from game.leads import (
    LeadLifecycle,
    LeadStatus,
    add_lead_relation,
    commit_session_lead_with_context,
    create_lead,
    ensure_lead_registry,
    get_lead,
    obsolete_session_lead,
    obsolete_superseded_lead,
    resolve_session_lead,
    upsert_lead,
)
from game.prompt_context import build_authoritative_lead_prompt_context

pytestmark = pytest.mark.integration


def _base_session(turn: int = 1) -> dict:
    return {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": turn}


def _base_world() -> dict:
    return {"inference_rules": [], "clues": {}}


def _base_scene(scene_id: str, discoverable_clues: list | None = None) -> dict:
    scene: dict = {"id": scene_id, "visible_facts": [], "exits": [], "mode": "exploration"}
    if discoverable_clues is not None:
        scene["discoverable_clues"] = discoverable_clues
    return {"scene": scene}


def _ids_in_compact_rows(rows):
    return [str(r.get("id") or "") for r in (rows or []) if isinstance(r, dict)]


def _lead_in_active_prompt_slice(pc: dict, lead_id: str) -> bool:
    lid = str(lead_id or "").strip()
    for key in ("top_active_leads", "currently_pursued_lead"):
        if key == "currently_pursued_lead":
            row = pc.get(key)
            if isinstance(row, dict) and str(row.get("id") or "").strip() == lid:
                return True
            continue
        for r in pc.get(key) or []:
            if isinstance(r, dict) and str(r.get("id") or "").strip() == lid:
                return True
    return False


def _journal_bucket_ids(journal: dict, key: str) -> list[str]:
    return [str(r.get("id") or "") for r in (journal.get(key) or []) if isinstance(r, dict)]


def _assert_in_active_prompt(context: dict, lead_id: str) -> None:
    top_ids = _ids_in_compact_rows(context.get("top_active_leads"))
    cp = context.get("currently_pursued_lead")
    assert _lead_in_active_prompt_slice(context, lead_id), (
        f"expected lead_id {lead_id!r} in authoritative prompt slice "
        f"(top_active_leads or currently_pursued_lead); "
        f"top_active_lead_ids={top_ids!r}, currently_pursued_lead={cp!r}"
    )


def _assert_not_in_active_prompt(context: dict, lead_id: str) -> None:
    top_ids = _ids_in_compact_rows(context.get("top_active_leads"))
    assert not _lead_in_active_prompt_slice(context, lead_id), (
        f"did not expect lead_id {lead_id!r} in authoritative prompt slice; "
        f"top_active_lead_ids={top_ids!r}, currently_pursued_lead={context.get('currently_pursued_lead')!r}"
    )


def _assert_bucket_ids(journal: dict, bucket_key: str, expected_ids: list[str]) -> None:
    actual = _journal_bucket_ids(journal, bucket_key)
    assert actual == expected_ids, (
        f"journal bucket {bucket_key!r} lead ids: expected {expected_ids!r}, got {actual!r}"
    )


# --- discovery ---


def test_lifecycle_slice_clue_discovery_creates_authoritative_lead():
    scene_id = "vertical_slice_lab"
    clue_id = "vertical_slice_clue"
    clue_text = "A scuffed brass tag stamped with a house sigil."
    session = _base_session()
    world = _base_world()
    envelope = _base_scene(
        scene_id,
        discoverable_clues=[{"id": clue_id, "text": clue_text}],
    )

    revealed = process_investigation_discovery(envelope, session, world=world)
    assert len(revealed) == 1

    reg = ensure_lead_registry(session)
    assert len(reg) == 1

    row = get_lead(session, clue_id)
    assert row is not None
    assert clue_id in (row.get("evidence_clue_ids") or [])
    assert str(row.get("lifecycle") or "") == "discovered"
    assert str(row.get("confidence") or "") == "plausible"

    journal = build_player_journal(session, world, envelope)
    assert clue_text in journal["discovered_clues"]
    active_rows = journal.get("active_leads") or []
    assert any(isinstance(r, dict) and str(r.get("id") or "") == clue_id for r in active_rows)

    pc = build_authoritative_lead_prompt_context(
        session, world, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    _assert_in_active_prompt(pc, clue_id)
    top_ids = _ids_in_compact_rows(pc.get("top_active_leads"))
    assert top_ids.count(clue_id) == 1, (
        f"top_active_leads: expected exactly one row for {clue_id!r}; ids={top_ids!r}"
    )


def test_lifecycle_slice_reinserting_same_clue_is_idempotent():
    scene_id = "vertical_slice_gate"
    clue_id = "vertical_slice_repeat"
    clue_text = "Same scratch marks on both doorposts."
    session = _base_session()
    world = _base_world()
    envelope = _base_scene(
        scene_id,
        discoverable_clues=[{"id": clue_id, "text": clue_text}],
    )

    first = process_investigation_discovery(envelope, session, world=world)
    assert len(first) == 1
    row_after_first = get_lead(session, clue_id)
    assert row_after_first is not None
    ev_first = list(row_after_first.get("evidence_clue_ids") or [])

    second = process_investigation_discovery(envelope, session, world=world)
    assert second == []

    dup = apply_authoritative_clue_discovery(
        session,
        scene_id,
        clue_id=clue_id,
        clue_text=clue_text,
        discovered_clues=[clue_text],
        world=world,
    )
    assert dup == []

    assert len(ensure_lead_registry(session)) == 1
    row_after = get_lead(session, clue_id)
    assert row_after is not None
    assert list(row_after.get("evidence_clue_ids") or []) == ev_first
    ev = list(row_after.get("evidence_clue_ids") or [])
    assert len(ev) == len(set(ev))

    pc = build_authoritative_lead_prompt_context(
        session, world, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    top_ids = _ids_in_compact_rows(pc.get("top_active_leads"))
    assert top_ids.count(clue_id) == 1, (
        f"top_active_leads: expected exactly one row for {clue_id!r} after idempotent re-discovery; ids={top_ids!r}"
    )

    journal = build_player_journal(session, world, envelope)
    active_rows = journal.get("active_leads") or []
    active_ids = [str(r.get("id") or "") for r in active_rows if isinstance(r, dict)]
    assert active_ids.count(clue_id) == 1, (
        f"journal active_leads: expected exactly one row for {clue_id!r}; ids={active_ids!r}"
    )


# --- reinforcement ---


def test_lifecycle_slice_second_signal_reinforces_confidence():
    scene_id = "vertical_slice_crime_scene"
    world = {
        "inference_rules": [],
        "clues": {
            "ev_alpha": {"canonical_lead_id": "murder_case", "type": "investigation"},
            "ev_beta": {"canonical_lead_id": "murder_case", "type": "investigation"},
        },
    }
    envelope = _base_scene(
        scene_id,
        discoverable_clues=[
            {"id": "ev_alpha", "text": "Witness saw a knife."},
            {"id": "ev_beta", "text": "Blood on the floor."},
        ],
    )
    session = _base_session()

    r1 = process_investigation_discovery(envelope, session, world=world)
    assert len(r1) == 1
    row1 = get_lead(session, "murder_case")
    assert row1 is not None
    cf1 = str(row1.get("confidence") or "")
    ev1 = list(row1.get("evidence_clue_ids") or [])

    r2 = process_investigation_discovery(envelope, session, world=world)
    assert len(r2) == 1
    row2 = get_lead(session, "murder_case")
    assert row2 is not None

    assert len(ensure_lead_registry(session)) == 1
    ev2 = list(row2.get("evidence_clue_ids") or [])
    assert len(ev2) > len(ev1)
    assert len(ev2) == len(set(ev2))

    cf2 = str(row2.get("confidence") or "")
    order = ("rumor", "plausible", "credible", "confirmed")
    assert order.index(cf2) > order.index(cf1)

    pc = build_authoritative_lead_prompt_context(
        session, world, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    _assert_in_active_prompt(pc, "murder_case")


# --- commitment ---


def test_lifecycle_slice_commitment_transitions():
    scene_id = "vertical_slice_commit"
    clue_id = "vertical_slice_commit_clue"
    clue_text = "A ledger page torn at the margin."
    turn = 6
    session = _base_session(turn=turn)
    world = _base_world()
    envelope = _base_scene(
        scene_id,
        discoverable_clues=[{"id": clue_id, "text": clue_text}],
    )

    revealed = process_investigation_discovery(envelope, session, world=world)
    assert len(revealed) == 1

    commit_kw = dict(
        turn=turn,
        commitment_source="vertical_slice_affordance",
        commitment_strength=2,
        next_step="Cross-check the shipping manifest",
    )
    commit_session_lead_with_context(session, clue_id, **commit_kw)
    row1 = get_lead(session, clue_id)
    assert row1 is not None
    assert str(row1.get("lifecycle") or "") == "committed"
    assert str(row1.get("status") or "") == "pursued"
    assert row1.get("committed_at_turn") == turn
    assert row1.get("commitment_source") == "vertical_slice_affordance"
    assert row1.get("commitment_strength") == 2
    assert row1.get("next_step") == "Cross-check the shipping manifest"

    snapshot = {
        "lifecycle": row1.get("lifecycle"),
        "status": row1.get("status"),
        "committed_at_turn": row1.get("committed_at_turn"),
        "commitment_source": row1.get("commitment_source"),
        "commitment_strength": row1.get("commitment_strength"),
        "next_step": row1.get("next_step"),
        "evidence_clue_ids": list(row1.get("evidence_clue_ids") or []),
    }

    commit_session_lead_with_context(session, clue_id, **commit_kw)
    assert len(ensure_lead_registry(session)) == 1
    row2 = get_lead(session, clue_id)
    assert row2 is not None
    assert {
        "lifecycle": row2.get("lifecycle"),
        "status": row2.get("status"),
        "committed_at_turn": row2.get("committed_at_turn"),
        "commitment_source": row2.get("commitment_source"),
        "commitment_strength": row2.get("commitment_strength"),
        "next_step": row2.get("next_step"),
        "evidence_clue_ids": list(row2.get("evidence_clue_ids") or []),
    } == snapshot

    pc = build_authoritative_lead_prompt_context(
        session, world, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    cp = pc.get("currently_pursued_lead")
    assert isinstance(cp, dict) and str(cp.get("id") or "") == clue_id
    _assert_in_active_prompt(pc, clue_id)
    top_ids = _ids_in_compact_rows(pc.get("top_active_leads"))
    assert top_ids.count(clue_id) == 1, (
        f"top_active_leads: expected committed lead {clue_id!r} once; ids={top_ids!r}"
    )


# --- resolution ---


def test_lifecycle_slice_resolution_removes_from_actionable():
    scene_id = "vertical_slice_resolve"
    clue_id = "vertical_slice_resolve_clue"
    clue_text = "A wax seal matching the courier's route book."
    session = _base_session()
    world = _base_world()
    envelope = _base_scene(
        scene_id,
        discoverable_clues=[{"id": clue_id, "text": clue_text}],
    )

    process_investigation_discovery(envelope, session, world=world)
    row = get_lead(session, clue_id)
    assert row is not None

    resolve_session_lead(
        session,
        clue_id,
        resolution_type="mystery solved",
        resolution_summary="Courier identified; thread closed.",
        turn=8,
        consequence_ids=["fx_slice_1"],
    )
    resolved = get_lead(session, clue_id)
    assert resolved is not None
    assert str(resolved.get("lifecycle") or "") == "resolved"
    assert str(resolved.get("status") or "") == "resolved"
    assert resolved.get("resolution_type") == "mystery solved"
    assert resolved.get("resolution_summary") == "Courier identified; thread closed."
    assert resolved.get("resolved_at_turn") == 8
    assert list(resolved.get("consequence_ids") or []) == ["fx_slice_1"]

    pc = build_authoritative_lead_prompt_context(
        session, world, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    top_ids = _ids_in_compact_rows(pc.get("top_active_leads"))
    assert clue_id not in top_ids, (
        f"top_active_leads: resolved lead {clue_id!r} must be absent; ids={top_ids!r}"
    )
    cp = pc.get("currently_pursued_lead")
    assert cp is None or str(cp.get("id") or "").strip() != clue_id
    _assert_not_in_active_prompt(pc, clue_id)

    # --- terminal visibility (journal buckets) ---
    journal = build_player_journal(session, world, envelope)
    for bucket in ("active_leads", "pursued_leads", "stale_leads"):
        bucket_ids = _journal_bucket_ids(journal, bucket)
        assert clue_id not in bucket_ids, (
            f"journal {bucket!r}: resolved lead {clue_id!r} must be absent; ids={bucket_ids!r}"
        )
    resolved_ids = _journal_bucket_ids(journal, "resolved_leads")
    assert clue_id in resolved_ids, (
        f"journal resolved_leads: expected {clue_id!r}; ids={resolved_ids!r}"
    )


# --- supersession ---


def test_lifecycle_slice_supersession_obsoletes_old_lead():
    scene_id = "vertical_slice_super"
    old_clue = "vertical_slice_super_old"
    new_clue = "vertical_slice_super_new"
    session = _base_session(turn=5)
    world = _base_world()
    envelope_old = _base_scene(
        scene_id,
        discoverable_clues=[{"id": old_clue, "text": "Old rumor about the side door."}],
    )
    process_investigation_discovery(envelope_old, session, world=world)
    assert get_lead(session, old_clue) is not None

    envelope_new = _base_scene(
        scene_id,
        discoverable_clues=[{"id": new_clue, "text": "Captain confirms the eastern route."}],
    )
    process_investigation_discovery(envelope_new, session, world=world)
    assert get_lead(session, new_clue) is not None

    obsolete_superseded_lead(session, old_clue, replaced_by_lead_id=new_clue, turn=5)
    old_row = get_lead(session, old_clue)
    new_row = get_lead(session, new_clue)
    assert old_row is not None
    assert new_row is not None
    assert str(old_row.get("lifecycle") or "") == "obsolete"
    assert old_row.get("obsolete_reason") == "superseded"
    assert str(old_row.get("superseded_by") or "") == new_clue

    pc = build_authoritative_lead_prompt_context(
        session, world, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    _assert_not_in_active_prompt(pc, old_clue)
    _assert_in_active_prompt(pc, new_clue)

    journal = build_player_journal(session, world, envelope_new)
    for bucket in ("active_leads", "pursued_leads", "stale_leads"):
        bucket_ids = _journal_bucket_ids(journal, bucket)
        assert old_clue not in bucket_ids, (
            f"journal {bucket!r}: superseded lead {old_clue!r} must be absent; ids={bucket_ids!r}"
        )
    obsolete_ids = _journal_bucket_ids(journal, "obsolete_leads")
    assert old_clue in obsolete_ids, (
        f"journal obsolete_leads: expected {old_clue!r}; ids={obsolete_ids!r}"
    )
    actionable = (
        _journal_bucket_ids(journal, "active_leads")
        + _journal_bucket_ids(journal, "pursued_leads")
        + _journal_bucket_ids(journal, "stale_leads")
    )
    assert new_clue in actionable, (
        f"journal actionable buckets: expected {new_clue!r} in active+pursued+stale; combined_ids={actionable!r}"
    )


# --- journal alignment ---


def test_lifecycle_slice_journal_matches_registry():
    session = _base_session()
    world = _base_world()
    envelope = _base_scene("vertical_slice_journal_mix")

    upsert_lead(
        session,
        create_lead(
            title="Active mix",
            summary="",
            id="mix_active",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    upsert_lead(
        session,
        create_lead(
            title="Pursued mix",
            summary="",
            id="mix_pursued",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    commit_session_lead_with_context(
        session,
        "mix_pursued",
        turn=2,
        commitment_source="mix_test",
        commitment_strength=1,
        next_step="Interview the harbor master",
    )
    upsert_lead(
        session,
        create_lead(
            title="Resolved mix",
            summary="",
            id="mix_resolved",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    resolve_session_lead(
        session,
        "mix_resolved",
        resolution_type="confirmed",
        resolution_summary="Closed at the dock",
        turn=3,
    )
    upsert_lead(
        session,
        create_lead(
            title="Obsolete mix",
            summary="",
            id="mix_obsolete",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    obsolete_session_lead(session, "mix_obsolete", obsolete_reason="withdrawn", turn=4)

    journal = build_player_journal(session, world, envelope)
    _assert_bucket_ids(journal, "active_leads", ["mix_active"])
    _assert_bucket_ids(journal, "pursued_leads", ["mix_pursued"])
    _assert_bucket_ids(journal, "resolved_leads", ["mix_resolved"])
    _assert_bucket_ids(journal, "obsolete_leads", ["mix_obsolete"])

    assert journal["lead_counts"]["total"] == 4
    assert journal["lead_counts"]["nonterminal"] == 2
    for bid in ("mix_resolved", "mix_obsolete"):
        for bucket in ("active_leads", "pursued_leads", "stale_leads"):
            bucket_ids = _journal_bucket_ids(journal, bucket)
            assert bid not in bucket_ids, (
                f"journal {bucket!r}: terminal lead {bid!r} must be absent; ids={bucket_ids!r}"
            )


# --- prompt-context contract ---


def test_lifecycle_slice_prompt_context_contract():
    turn = 10
    session = _base_session(turn=turn)
    world = _base_world()

    upsert_lead(
        session,
        create_lead(
            title="Pursued contract",
            summary="",
            id="slice_pursued",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            priority=5,
        ),
    )
    commit_session_lead_with_context(
        session,
        "slice_pursued",
        turn=9,
        commitment_source="contract_pursue",
        commitment_strength=3,
        next_step="Secure the affidavit",
    )
    upsert_lead(
        session,
        create_lead(
            title="Active contract",
            summary="",
            id="slice_active",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            priority=1,
        ),
    )
    upsert_lead(
        session,
        create_lead(
            title="Obsolete contract",
            summary="",
            id="slice_obsolete",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
        ),
    )
    obsolete_session_lead(session, "slice_obsolete", obsolete_reason="irrelevant", turn=8)

    upsert_lead(
        session,
        create_lead(
            title="Recent touch contract",
            summary="",
            id="slice_recent",
            lifecycle=LeadLifecycle.DISCOVERED,
            status=LeadStatus.ACTIVE,
            priority=1,
        ),
    )
    add_lead_relation(session, "slice_recent", "related_npc_ids", "npc_contract_anchor", turn=turn)

    pc = build_authoritative_lead_prompt_context(
        session, world, public_scene={}, runtime={}, recent_log=[], active_npc_id=None
    )
    cp = pc.get("currently_pursued_lead")
    assert isinstance(cp, dict) and str(cp.get("id") or "") == "slice_pursued"

    top_ids = _ids_in_compact_rows(pc.get("top_active_leads"))
    assert "slice_obsolete" not in top_ids, (
        f"top_active_leads: obsolete lead must be omitted; ids={top_ids!r}"
    )
    assert len(top_ids) == len(set(top_ids)), (
        f"top_active_leads: duplicate compact rows; ids={top_ids!r}"
    )

    _assert_in_active_prompt(pc, "slice_pursued")
    _assert_in_active_prompt(pc, "slice_active")
    _assert_not_in_active_prompt(pc, "slice_obsolete")

    recent_rows = pc.get("recent_lead_changes") or []
    assert any(isinstance(r, dict) and str(r.get("id") or "") == "slice_recent" for r in recent_rows)
