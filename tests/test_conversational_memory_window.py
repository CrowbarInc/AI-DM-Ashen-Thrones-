"""Unit tests for Objective #15 conversational memory selector (game.conversational_memory_window).

Deterministic only — no model calls or network.
"""
from __future__ import annotations

import pytest

from game.conversational_memory_window import (
    ANCHORED_INTERLOCUTOR_BONUS,
    ACTIVE_INTERACTION_TARGET_BONUS,
    ACTIVE_SCENE_ENTITY_HIT_WEIGHT,
    EXPLICIT_REINTRO_ENTITY_BONUS,
    EXPLICIT_REINTRO_TOPIC_BONUS,
    INACTIVE_PENALTY_WEIGHT,
    RECENCY_WEIGHT,
    RECENT_TURN_KIND_BONUS,
    STALE_PENALTY_WEIGHT,
    WINDOW_VERSION,
    _extract_explicit_reintroductions,
    _is_candidate_stale,
    _normalize_memory_candidate,
    _score_memory_candidate,
    active_scene_entity_bonus,
    build_conversational_memory_window_contract,
    explicit_reintroduction_bonus,
    inactive_penalty,
    interaction_anchor_bonuses,
    recency_score,
    select_conversational_memory_window,
    stale_penalty,
)


# --- A. Contract construction -------------------------------------------------


def test_build_contract_v1_shape_and_defaults():
    c = build_conversational_memory_window_contract()
    assert c["window_version"] == WINDOW_VERSION == "v1"
    assert c["enabled"] is True
    assert c["prioritize_recent_turns"] is True
    assert c["prioritize_active_scene_entities"] is True
    assert c["deprioritize_stale_inactive_elements"] is True
    assert c["allow_explicit_reintroduction"] is True
    assert c["recent_turn_window"] == 6
    assert c["soft_memory_limit"] == 12
    assert c["stale_after_turns"] == 18
    assert c["active_scene_entity_ids"] == []
    assert c["anchored_interlocutor_id"] == ""
    assert c["active_interaction_target_id"] == ""
    assert c["explicit_reintroduced_entity_ids"] == []
    assert c["explicit_reintroduced_topics"] == []
    dbg = c["selection_debug"]
    assert dbg["source_of_activity_anchor"] == "unspecified"
    assert dbg["source_of_recentness"] == "unspecified"
    assert dbg["source_of_reintroductions"] == "unspecified"


def test_build_contract_normalizes_ids_and_topics():
    c = build_conversational_memory_window_contract(
        active_scene_entity_ids=[" Zeta ", "alpha", "alpha", "Beta "],
        explicit_reintroduced_entity_ids=["NPC_A", "npc_a"],
        explicit_reintroduced_topics=["  Smuggling ", "smuggling", "Patrol"],
    )
    assert c["active_scene_entity_ids"] == ["alpha", "beta", "zeta"]
    assert c["explicit_reintroduced_entity_ids"] == ["npc_a"]
    assert c["explicit_reintroduced_topics"] == ["patrol", "smuggling"]


def test_build_contract_selection_debug_merge_preserves_omitted_defaults():
    c = build_conversational_memory_window_contract(
        selection_debug={"source_of_recentness": "custom"},
        source_of_activity_anchor="",
        source_of_reintroductions="",
    )
    dbg = c["selection_debug"]
    assert dbg["source_of_recentness"] == "custom"
    assert dbg["source_of_activity_anchor"] == "unspecified"
    assert dbg["source_of_reintroductions"] == "unspecified"


def test_build_contract_explicit_string_sources_fill_debug():
    c = build_conversational_memory_window_contract(
        source_of_activity_anchor="visibility",
        source_of_recentness="turn_counter",
        source_of_reintroductions="aliases",
    )
    dbg = c["selection_debug"]
    assert dbg["source_of_activity_anchor"] == "visibility"
    assert dbg["source_of_recentness"] == "turn_counter"
    assert dbg["source_of_reintroductions"] == "aliases"


# --- B. Scoring primitives ----------------------------------------------------


def test_recency_linear_within_window_and_zero_outside():
    rw = 6
    ct = 20
    # age 0 -> full ramp term (rw - 0 + 1) / (rw + 1)
    expected_newest = RECENCY_WEIGHT * (rw + 1) / (rw + 1)
    assert recency_score(20, ct, recent_turn_window=rw, prioritize_recent_turns=True) == pytest.approx(
        expected_newest
    )
    # age 6 (boundary): still in window
    assert recency_score(14, ct, recent_turn_window=rw, prioritize_recent_turns=True) > 0
    # age 7: outside
    assert recency_score(13, ct, recent_turn_window=rw, prioritize_recent_turns=True) == 0.0
    assert recency_score(None, ct, recent_turn_window=rw, prioritize_recent_turns=True) == 0.0


def test_recency_disabled_returns_zero():
    assert (
        recency_score(20, 20, recent_turn_window=6, prioritize_recent_turns=False) == 0.0
    )


def test_active_scene_entity_bonus_scales_with_hits():
    scene = ["a", "b"]
    assert active_scene_entity_bonus(["a"], scene, prioritize_active_scene_entities=True) == pytest.approx(
        1 * ACTIVE_SCENE_ENTITY_HIT_WEIGHT
    )
    assert active_scene_entity_bonus(["a", "b"], scene, prioritize_active_scene_entities=True) == pytest.approx(
        2 * ACTIVE_SCENE_ENTITY_HIT_WEIGHT
    )
    assert active_scene_entity_bonus([], scene, prioritize_active_scene_entities=True) == 0.0


def test_interaction_anchor_bonuses_split():
    tb, ab = interaction_anchor_bonuses(
        ["npc_t", "other"],
        active_interaction_target_id="npc_t",
        anchored_interlocutor_id="npc_a",
    )
    assert tb == pytest.approx(ACTIVE_INTERACTION_TARGET_BONUS)
    assert ab == 0.0
    tb2, ab2 = interaction_anchor_bonuses(
        ["npc_a"],
        active_interaction_target_id="npc_t",
        anchored_interlocutor_id="npc_a",
    )
    assert tb2 == 0.0
    assert ab2 == pytest.approx(ANCHORED_INTERLOCUTOR_BONUS)


def test_explicit_reintroduction_bonus_entity_and_topic():
    s = explicit_reintroduction_bonus(
        ["e1", "e2"],
        ["alpha", "beta"],
        explicit_reintroduced_entity_ids=["e1"],
        explicit_reintroduced_topics=["alpha"],
        allow_explicit_reintroduction=True,
    )
    assert s == pytest.approx(EXPLICIT_REINTRO_ENTITY_BONUS + EXPLICIT_REINTRO_TOPIC_BONUS)


def test_stale_penalty_only_when_stale_and_not_exempt():
    assert (
        stale_penalty(1, 30, stale_after_turns=18, deprioritize=True, exempt=False)
        == pytest.approx(STALE_PENALTY_WEIGHT)
    )
    assert stale_penalty(15, 30, stale_after_turns=18, deprioritize=True, exempt=False) == 0.0
    assert stale_penalty(1, 30, stale_after_turns=18, deprioritize=True, exempt=True) == 0.0
    assert stale_penalty(None, 30, stale_after_turns=18, deprioritize=True, exempt=False) == 0.0


def test_inactive_penalty_gatekeepers():
    assert inactive_penalty(
        has_active_scene_overlap=False,
        is_recent=False,
        is_anchor_or_target=False,
        is_explicit_reintro=False,
        deprioritize_stale_inactive=True,
    ) == pytest.approx(INACTIVE_PENALTY_WEIGHT)
    for kwargs in (
        dict(has_active_scene_overlap=True, is_recent=False, is_anchor_or_target=False, is_explicit_reintro=False),
        dict(has_active_scene_overlap=False, is_recent=True, is_anchor_or_target=False, is_explicit_reintro=False),
        dict(has_active_scene_overlap=False, is_recent=False, is_anchor_or_target=True, is_explicit_reintro=False),
        dict(has_active_scene_overlap=False, is_recent=False, is_anchor_or_target=False, is_explicit_reintro=True),
    ):
        assert (
            inactive_penalty(**kwargs, deprioritize_stale_inactive=True) == 0.0
        )


def test_inactive_penalty_disabled():
    assert (
        inactive_penalty(
            has_active_scene_overlap=False,
            is_recent=False,
            is_anchor_or_target=False,
            is_explicit_reintro=False,
            deprioritize_stale_inactive=False,
        )
        == 0.0
    )


# --- C. Stale exemption (via _score_memory_candidate reasons / stale_penalty) --


def _base_contract(**overrides):
    c = build_conversational_memory_window_contract(
        recent_turn_window=4,
        stale_after_turns=10,
        soft_memory_limit=12,
        active_scene_entity_ids=["scene_e"],
        anchored_interlocutor_id="anc_e",
        active_interaction_target_id="tgt_e",
        explicit_reintroduced_entity_ids=["re_e"],
        explicit_reintroduced_topics=["smuggling"],
    )
    c.update(overrides)
    return c


def test_stale_exempt_recent_window():
    # Need age > stale_after (stale) and age <= recent_turn_window (recent) — requires rw > stale_after.
    c = _base_contract(recent_turn_window=10, stale_after_turns=3)
    norm = {"kind": "x", "entity_ids": [], "topic_tokens": [], "source_turn": 96, "text": "t"}
    _, _, reasons = _score_memory_candidate(norm, c, current_turn=100)
    assert "stale_exempt" in reasons  # age 4 > 3 (stale) and 4 <= 10 (recent-window exempt)
    assert "stale_penalty" not in reasons


def test_stale_exempt_active_scene_overlap():
    c = _base_contract()
    norm = {"kind": "x", "entity_ids": ["scene_e"], "topic_tokens": [], "source_turn": 80, "text": "t"}
    _, _, reasons = _score_memory_candidate(norm, c, current_turn=100)
    assert "stale_exempt" in reasons
    assert "active_scene_entity" in reasons


def test_stale_exempt_active_target_and_interlocutor():
    c = _base_contract()
    n1 = {"kind": "x", "entity_ids": ["tgt_e"], "topic_tokens": [], "source_turn": 80, "text": "t"}
    _, _, r1 = _score_memory_candidate(n1, c, current_turn=100)
    assert "stale_exempt" in r1
    assert "active_interaction_target" in r1
    n2 = {"kind": "x", "entity_ids": ["anc_e"], "topic_tokens": [], "source_turn": 80, "text": "t"}
    _, _, r2 = _score_memory_candidate(n2, c, current_turn=100)
    assert "stale_exempt" in r2
    assert "anchored_interlocutor" in r2


def test_stale_exempt_explicit_reintroduction_bonus_path():
    c = _base_contract()
    norm = {
        "kind": "x",
        "entity_ids": ["re_e"],
        "topic_tokens": [],
        "source_turn": 80,
        "text": "t",
    }
    _, _, reasons = _score_memory_candidate(norm, c, current_turn=100)
    assert "explicit_reintroduction" in reasons
    assert "stale_exempt" in reasons


def test_formerly_hot_disconnected_entity_not_exempt_from_stale_penalty():
    c = _base_contract(
        explicit_reintroduced_entity_ids=[],
        explicit_reintroduced_topics=[],
    )
    norm = {
        "kind": "x",
        "entity_ids": ["old_friend_npc"],
        "topic_tokens": [],
        "source_turn": 80,
        "text": "t",
    }
    total, breakdown, reasons = _score_memory_candidate(norm, c, current_turn=100)
    assert "stale_exempt" not in reasons
    assert "stale_penalty" in reasons
    assert breakdown["stale_penalty"] > 0


# --- D. Explicit reintroduction narrowness ------------------------------------


def test_extract_entity_multiword_alias_phrase():
    ent, top, dbg = _extract_explicit_reintroductions(
        "Tell me again about the northern watch captain.",
        entity_alias_map={"npc_captain": ["northern watch captain", "captain"]},
    )
    assert "npc_captain" in ent
    assert "matched_entity_ids" in dbg


def test_extract_grounded_interlocutor_alias():
    ent, _top, dbg = _extract_explicit_reintroductions(
        "Kethro said nothing useful earlier.",
        entity_alias_map={
            "npc_kethro": ["Kethro"],
        },
        anchored_interlocutor_id="npc_kethro",
        active_interaction_target_id="",
    )
    assert "npc_kethro" in ent
    assert any(x.get("id") == "npc_kethro" for x in dbg.get("matched_grounded_ids", []))


def test_extract_topic_requires_callback_and_anchor_token():
    ent, top, dbg = _extract_explicit_reintroductions(
        "Earlier we discussed the patrol routes near the river.",
        entity_alias_map={},
        topic_anchor_tokens=["patrol", "river"],
    )
    assert "patrol" in top or "river" in top
    assert dbg.get("callback_marker_hit") is not None

    _e, top2, dbg2 = _extract_explicit_reintroductions(
        "Patrol routes near the river are dangerous.",
        entity_alias_map={},
        topic_anchor_tokens=["patrol"],
    )
    assert top2 == []
    assert dbg2.get("callback_marker_hit") is None


def test_extract_no_match_from_unmapped_lexical_overlap():
    ent, top, _d = _extract_explicit_reintroductions(
        "The smuggling ring and the harbor taxes are connected somehow.",
        entity_alias_map={"npc_x": ["unrelated moniker"]},
        topic_anchor_tokens=["smuggling"],
    )
    assert ent == []
    assert top == []


def test_extract_single_token_alias_length_rules():
    ent, _t, _d = _extract_explicit_reintroductions(
        "I trust aldrin completely.",
        entity_alias_map={"npc_a": ["aldrin"]},
    )
    assert "npc_a" in ent
    ent2, _, _ = _extract_explicit_reintroductions(
        "I trust bob completely.",
        entity_alias_map={"npc_b": ["bob"]},
    )
    assert "npc_b" in ent2  # len 3 single-token aliases match when present as a word
    ent3, _, _ = _extract_explicit_reintroductions(
        "go to ed",
        entity_alias_map={"npc_ed": ["ed"]},
    )
    assert "npc_ed" not in ent3  # below minimum length for single-token match


def test_extract_disabled_returns_empty():
    ent, top, dbg = _extract_explicit_reintroductions(
        "we discussed smuggling earlier",
        entity_alias_map={"a": ["smuggling"]},
        allow_explicit_reintroduction=False,
    )
    assert ent == [] and top == []
    assert dbg.get("reason") == "disabled"


# --- E. Normalization / stale flag / selector ---------------------------------


def test_normalize_memory_candidate_sorts_and_defaults():
    n = _normalize_memory_candidate(
        {
            "kind": "",
            "entity_ids": ["Z", "a", "a"],
            "topic_tokens": ["Beta", "beta"],
            "source_turn": "15",
            "text": "  hi  ",
        }
    )
    assert n["kind"] == "unknown"
    assert n["entity_ids"] == ["a", "z"]
    assert n["topic_tokens"] == ["beta"]
    assert n["source_turn"] == 15
    assert n["text"] == "hi"


def test_is_candidate_stale():
    assert _is_candidate_stale(5, 30, stale_after_turns=10) is True
    assert _is_candidate_stale(20, 30, stale_after_turns=10) is False
    assert _is_candidate_stale(None, 30, stale_after_turns=10) is False


def test_score_memory_candidate_recent_turn_kind_bonus():
    c = build_conversational_memory_window_contract(recent_turn_window=6, stale_after_turns=50)
    norm = {
        "kind": "recent_turn",
        "entity_ids": [],
        "topic_tokens": [],
        "source_turn": 10,
        "text": "t",
    }
    _total, br, reasons = _score_memory_candidate(norm, c, current_turn=10)
    assert br["recent_turn_kind_bonus"] == pytest.approx(RECENT_TURN_KIND_BONUS)
    assert "recent_turn_kind" in reasons


def test_score_memory_candidate_skips_inactive_penalty_when_source_turn_unknown():
    c = build_conversational_memory_window_contract(
        recent_turn_window=2,
        stale_after_turns=5,
        active_scene_entity_ids=[],
    )
    norm = {"kind": "recent_turn", "entity_ids": [], "topic_tokens": [], "source_turn": None, "text": "t"}
    _t, br, reasons = _score_memory_candidate(norm, c, current_turn=100)
    assert br["inactive_penalty"] == 0.0
    assert "inactive_penalty" not in reasons


def test_select_recent_beats_old_unrelated():
    c = build_conversational_memory_window_contract(
        soft_memory_limit=5,
        recent_turn_window=8,
        stale_after_turns=12,
        prioritize_active_scene_entities=False,
    )
    candidates = [
        {
            "kind": "recent_turn",
            "entity_ids": [],
            "topic_tokens": [],
            "source_turn": 5,
            "text": "old",
        },
        {
            "kind": "recent_turn",
            "entity_ids": [],
            "topic_tokens": [],
            "source_turn": 19,
            "text": "new",
        },
    ]
    out = select_conversational_memory_window(candidates, c, current_turn=20)
    assert out[0]["text"] == "new"


def test_select_old_anchor_survives_against_stale_noise():
    c = build_conversational_memory_window_contract(
        soft_memory_limit=3,
        recent_turn_window=4,
        stale_after_turns=8,
        active_scene_entity_ids=["keep"],
        anchored_interlocutor_id="keep",
    )
    candidates = [
        {
            "kind": "recent_turn",
            "entity_ids": ["noise"],
            "topic_tokens": [],
            "source_turn": 18,
            "text": "stale side",
        },
        {
            "kind": "npc_lead_discussion",
            "entity_ids": ["keep"],
            "topic_tokens": ["harbor"],
            "source_turn": 12,
            "text": "Lead: harbor (hinted)",
        },
    ]
    out = select_conversational_memory_window(candidates, c, current_turn=20)
    texts = [x["text"] for x in out]
    assert any("Lead:" in t for t in texts)


def test_select_deterministic_tie_break():
    c = build_conversational_memory_window_contract(soft_memory_limit=10, recent_turn_window=10)
    candidates = [
        {"kind": "b_kind", "entity_ids": [], "topic_tokens": [], "source_turn": 5, "text": "aaa"},
        {"kind": "b_kind", "entity_ids": [], "topic_tokens": [], "source_turn": 5, "text": "bbb"},
        {"kind": "a_kind", "entity_ids": [], "topic_tokens": [], "source_turn": 5, "text": "zzz"},
    ]
    out = select_conversational_memory_window(candidates, c, current_turn=10)
    # Same total score -> sort by kind asc, then -source_turn, then text
    kinds = [x["kind"] for x in out]
    assert kinds == sorted(kinds)


def test_select_soft_memory_limit():
    c = build_conversational_memory_window_contract(soft_memory_limit=2, recent_turn_window=20)
    candidates = [
        {"kind": "recent_turn", "entity_ids": [], "topic_tokens": [], "source_turn": n, "text": str(n)}
        for n in range(10)
    ]
    out = select_conversational_memory_window(candidates, c, current_turn=20)
    assert len(out) == 2


def test_select_disabled_or_zero_cap_returns_empty():
    c = build_conversational_memory_window_contract(enabled=False, soft_memory_limit=5)
    assert select_conversational_memory_window([{"kind": "x", "source_turn": 1, "text": "a"}], c, current_turn=2) == []
    c2 = build_conversational_memory_window_contract(enabled=True, soft_memory_limit=0)
    assert select_conversational_memory_window([{"kind": "x", "source_turn": 1, "text": "a"}], c2, current_turn=2) == []


def test_select_non_mapping_candidates_skipped():
    c = build_conversational_memory_window_contract(soft_memory_limit=5)
    out = select_conversational_memory_window(
        ["bad", {"kind": "recent_turn", "entity_ids": [], "topic_tokens": [], "source_turn": 1, "text": "ok"}],
        c,
        current_turn=2,
    )
    assert len(out) == 1
    assert out[0]["text"] == "ok"


def test_select_why_selected_tags_present():
    c = build_conversational_memory_window_contract(
        recent_turn_window=6,
        stale_after_turns=30,
        active_scene_entity_ids=["e1"],
    )
    cand = {
        "kind": "recent_turn",
        "entity_ids": ["e1"],
        "topic_tokens": [],
        "source_turn": 10,
        "text": "x",
    }
    out = select_conversational_memory_window([cand], c, current_turn=10)
    why = out[0].get("why_selected") or []
    assert "recency" in why
    assert "recent_turn_kind" in why
    assert "active_scene_entity" in why
