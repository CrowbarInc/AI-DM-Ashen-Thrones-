"""Engine-owned apply_engine_lead_signal: registry upsert, monotonic promotion, idempotence."""

from __future__ import annotations

from game.leads import (
    SESSION_LEAD_REGISTRY_KEY,
    apply_engine_lead_signal,
    ensure_lead_registry,
    get_lead,
)


def test_explicit_discovery_creates_lead_in_registry():
    session: dict = {}
    r = apply_engine_lead_signal(
        session,
        lead_id="lead_smithy",
        title="The hidden smithy",
        summary="Forge marks point east.",
        lead_type="investigation",
        source_kind="clue_explicit",
        presentation_level="explicit",
        source_scene_id="market",
        trigger_clue_id="clue_forge",
        turn=1,
    )
    assert r["status"] == "created"
    assert r["lead_id"] == "lead_smithy"
    reg = ensure_lead_registry(session)
    assert len(reg) == 1
    row = get_lead(session, "lead_smithy")
    assert row is not None
    assert row["lifecycle"] == "discovered"
    assert row["confidence"] == "plausible"
    assert "market" in row["related_scene_ids"]
    assert row["evidence_clue_ids"] == ["clue_forge"]


def test_identical_replay_is_idempotent():
    session: dict = {}
    kwargs = dict(
        lead_id="stable_lead",
        title="Stable",
        summary="Same signal twice.",
        source_kind="clue_explicit",
        presentation_level="explicit",
        trigger_clue_id="c1",
        turn=2,
    )
    a = apply_engine_lead_signal(session, **kwargs)
    b = apply_engine_lead_signal(session, **kwargs)
    assert a["status"] == "created"
    assert b["status"] == "unchanged"
    assert len(ensure_lead_registry(session)) == 1


def test_weaker_replay_does_not_downgrade():
    session: dict = {}
    apply_engine_lead_signal(
        session,
        lead_id="mono",
        title="Mono",
        summary="First",
        source_kind="clue_explicit",
        presentation_level="explicit",
        confidence="credible",
        turn=1,
    )
    row_before = dict(get_lead(session, "mono") or {})
    out = apply_engine_lead_signal(
        session,
        lead_id="mono",
        title="Mono",
        summary="First",
        source_kind="clue_inference",
        presentation_level="implicit",
        turn=2,
    )
    row_after = get_lead(session, "mono")
    assert row_after is not None
    assert row_after["lifecycle"] == row_before["lifecycle"] == "discovered"
    assert row_after["confidence"] == row_before["confidence"] == "credible"
    # Lifecycle/confidence stay monotonic; discovery_source may append a weaker audit label.
    assert out["status"] in ("unchanged", "updated")


def test_stronger_later_signal_promotes_same_lead():
    session: dict = {}
    apply_engine_lead_signal(
        session,
        lead_id="grow",
        title="Grow",
        summary="Whisper",
        source_kind="clue_inference",
        presentation_level="implicit",
        turn=1,
    )
    assert get_lead(session, "grow")["lifecycle"] == "hinted"
    out = apply_engine_lead_signal(
        session,
        lead_id="grow",
        title="Grow",
        summary="Whisper",
        source_kind="social",
        presentation_level="implicit",
        turn=2,
    )
    row = get_lead(session, "grow")
    assert row is not None
    assert row["lifecycle"] == "discovered"
    assert out["status"] == "updated"
    assert out["promotion_applied"] is True
    assert len(session[SESSION_LEAD_REGISTRY_KEY]) == 1


def test_evidence_and_related_merges_are_deduped():
    session: dict = {}
    apply_engine_lead_signal(
        session,
        lead_id="dedupe",
        title="Dedupe",
        summary="",
        source_kind="clue_explicit",
        presentation_level="explicit",
        source_scene_id="a",
        target_scene_id="b",
        source_npc_id="npc1",
        target_npc_id="npc1",
        trigger_clue_id="e1",
        tags=["t1", "t1"],
        turn=1,
    )
    r2 = apply_engine_lead_signal(
        session,
        lead_id="dedupe",
        title="Dedupe",
        summary="",
        source_kind="clue_explicit",
        presentation_level="explicit",
        source_scene_id="a",
        target_scene_id="b",
        trigger_clue_id="e1",
        tags=["t1"],
        turn=2,
    )
    assert r2["status"] == "unchanged"
    row = get_lead(session, "dedupe")
    assert row is not None
    assert row["related_scene_ids"] == ["a", "b"]
    assert row["related_npc_ids"] == ["npc1"]
    assert row["evidence_clue_ids"] == ["e1"]
    assert row["tags"] == ["t1"]
    assert r2["compat_pending_lead_needed"] is True


def test_second_distinct_trigger_corroborates_confidence():
    session: dict = {}
    apply_engine_lead_signal(
        session,
        lead_id="corr",
        title="Corroboration",
        summary="",
        source_kind="clue_explicit",
        presentation_level="explicit",
        trigger_clue_id="e_a",
        turn=1,
    )
    assert get_lead(session, "corr")["confidence"] == "plausible"
    apply_engine_lead_signal(
        session,
        lead_id="corr",
        title="Corroboration",
        summary="",
        source_kind="clue_explicit",
        presentation_level="explicit",
        trigger_clue_id="e_b",
        turn=2,
    )
    assert get_lead(session, "corr")["confidence"] == "credible"
