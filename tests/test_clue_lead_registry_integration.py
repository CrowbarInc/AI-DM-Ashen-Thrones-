"""Clue gateway writes authoritative leads via apply_engine_lead_signal (Block 2)."""

from __future__ import annotations

from game.clues import apply_authoritative_clue_discovery, record_discovered_clue, run_inference
from game.leads import SESSION_LEAD_REGISTRY_KEY, ensure_lead_registry, get_lead


def test_explicit_discovery_creates_authoritative_lead():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    r = record_discovered_clue(session, "gate", "patrol_clue", clue_text="Tracks lead east.")
    assert r["authoritative_lead_status"] == "created"
    assert r["authoritative_lead_id"] == "patrol_clue"
    reg = ensure_lead_registry(session)
    assert "patrol_clue" in reg
    row = get_lead(session, "patrol_clue")
    assert row is not None
    assert row["evidence_clue_ids"] == ["patrol_clue"]
    assert "gate" in row["related_scene_ids"]


def test_duplicate_discovery_idempotent_for_clues_and_leads():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    r1 = record_discovered_clue(session, "gate", "c1", clue_text="A")
    r2 = record_discovered_clue(session, "gate", "c1", clue_text="A")
    assert r1["authoritative_lead_status"] == "created"
    assert r2["authoritative_lead_status"] == "unchanged"
    assert len(ensure_lead_registry(session)) == 1


def test_inference_then_explicit_promotes_same_lead_row():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = {
        "inference_rules": [
            {
                "inferred_clue_id": "synth",
                "requires": ["a", "b"],
                "inferred_clue_text": "Synthesized conclusion.",
            }
        ],
        "clues": {},
    }
    from game.clues import add_clue_to_knowledge

    add_clue_to_knowledge(session, "a", "discovered", clue_text="A piece.")
    add_clue_to_knowledge(session, "b", "discovered", clue_text="B piece.")
    run_inference(session, world)
    assert session["clue_knowledge"]["synth"]["state"] == "inferred"

    row_inf = get_lead(session, "synth")
    assert row_inf is not None
    assert row_inf["lifecycle"] == "hinted"
    assert row_inf["confidence"] == "rumor"

    dup = record_discovered_clue(session, "gate", "synth", clue_text="Synthesized conclusion.")
    assert dup["status"] == "duplicate_ignored"
    assert dup["authoritative_lead_status"] == "updated"
    row_exp = get_lead(session, "synth")
    assert row_exp is not None
    assert row_exp["lifecycle"] == "discovered"
    assert row_exp["confidence"] == "plausible"
    assert len(session[SESSION_LEAD_REGISTRY_KEY]) == 1


def test_two_evidence_clues_same_canonical_lead_corroborate():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = {
        "clues": {
            "ev_alpha": {"canonical_lead_id": "murder_case", "type": "investigation"},
            "ev_beta": {"canonical_lead_id": "murder_case", "type": "investigation"},
        },
        "inference_rules": [],
    }
    record_discovered_clue(session, "s1", "ev_alpha", clue_text="Witness saw a knife.", world=world)
    row1 = get_lead(session, "murder_case")
    assert row1 is not None
    assert row1["confidence"] == "plausible"
    assert row1["evidence_clue_ids"] == ["ev_alpha"]

    record_discovered_clue(session, "s1", "ev_beta", clue_text="Blood on the floor.", world=world)
    row2 = get_lead(session, "murder_case")
    assert row2 is not None
    assert row2["confidence"] == "credible"
    assert row2["evidence_clue_ids"] == ["ev_alpha", "ev_beta"]
    assert len(ensure_lead_registry(session)) == 1


def test_replay_same_evidence_clue_no_extra_corroboration_bump():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = {
        "clues": {
            "ev_alpha": {"canonical_lead_id": "murder_case"},
            "ev_beta": {"canonical_lead_id": "murder_case"},
        },
        "inference_rules": [],
    }
    record_discovered_clue(session, "s1", "ev_alpha", clue_text="A", world=world)
    record_discovered_clue(session, "s1", "ev_beta", clue_text="B", world=world)
    cf_before = get_lead(session, "murder_case")["confidence"]
    r = record_discovered_clue(session, "s1", "ev_beta", clue_text="B", world=world)
    assert r["status"] == "duplicate_ignored"
    assert r["authoritative_lead_status"] == "unchanged"
    assert get_lead(session, "murder_case")["confidence"] == cf_before


def test_apply_authoritative_clue_discovery_preserves_runtime_and_registry():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 2}
    added = apply_authoritative_clue_discovery(
        session,
        "lab",
        clue_id="residue",
        clue_text="A faint residue.",
        discovered_clues=["A faint residue."],
    )
    assert added == ["A faint residue."]
    assert session["scene_runtime"]["lab"]["discovered_clue_ids"] == ["residue"]
    assert "residue" in session["clue_knowledge"]
    assert get_lead(session, "residue") is not None


def test_structured_clue_passes_target_for_compat_signal():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    structured = {"leads_to_scene": "river_road_ambush", "leads_to_npc": "watch_captain"}
    from unittest.mock import patch

    from game.leads import apply_engine_lead_signal as real_apply

    captured: dict = {}

    def capture_apply(s, **kwargs):
        captured.update(kwargs)
        return real_apply(s, **kwargs)

    with patch("game.clues.apply_engine_lead_signal", side_effect=capture_apply):
        record_discovered_clue(
            session,
            "gate",
            "tracks",
            clue_text="Bootprints.",
            structured_clue=structured,
        )
    assert captured.get("target_scene_id") == "river_road_ambush"
    assert captured.get("target_npc_id") == "watch_captain"
