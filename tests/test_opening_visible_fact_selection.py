"""Regression tests for opening-scene visible fact curation.

This module owns `game.opening_visible_fact_selection`, while any prompt-context
calls here are downstream smoke for opening-turn integration only.
"""
from __future__ import annotations

import importlib

from game.opening_visible_fact_selection import (
    OPENING_NARRATION_VISIBLE_FACT_MAX,
    is_opening_eligible_fact,
    opening_fact_primary_category,
    select_opening_narration_visible_facts,
    select_opening_narration_visible_facts_with_telemetry,
)

build_narration_context = importlib.import_module("game.prompt_context").build_narration_context


def _opening_session() -> dict:
    return {
        "active_scene_id": "frontier_gate",
        "response_mode": "standard",
        "turn_counter": 0,
        "visited_scene_ids": [],
        "interaction_context": {"active_interaction_target_id": None, "interaction_mode": "none"},
    }


def _minimal_ctx_kwargs(public_scene: dict) -> dict:
    return {
        "campaign": {"title": "T", "premise": "p", "character_role": "r", "gm_guidance": [], "world_pressures": []},
        "world": {"world_state": {"flags": {}, "counters": {}, "clocks": {}}, "event_log": [], "factions": []},
        "session": _opening_session(),
        "character": {"name": "G", "hp": {}, "ac": {}},
        "scene": {"scene": {**public_scene, "discoverable_clues": [], "hidden_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "Begin.",
        "resolution": None,
        "scene_runtime": {},
        "public_scene": public_scene,
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["general"]},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
    }


def test_opening_selection_respects_budget():
    facts = [f"Distinct environmental beat number {i} at the stone gate." for i in range(20)]
    public = {
        "id": "frontier_gate",
        "location": "Gate",
        "summary": "Gate scene.",
        "visible_facts": facts,
        "exits": [],
        "enemies": [],
    }
    out = select_opening_narration_visible_facts(public)
    assert len(out) <= OPENING_NARRATION_VISIBLE_FACT_MAX
    ctx = build_narration_context(**_minimal_ctx_kwargs(public))
    assert ctx["narration_obligations"]["is_opening_scene"] is True
    assert len(ctx["narration_visibility"]["visible_facts"]) <= OPENING_NARRATION_VISIBLE_FACT_MAX


def test_opening_selection_collapses_patrol_duplicates():
    public = {
        "id": "test",
        "location": "Road",
        "summary": "Road.",
        "visible_facts": [
            "The last patrol has not returned from the north road.",
            "Rumors say the night patrol is missing.",
            "Mud slicks the checkpoint stones.",
            "Refugees mutter about the missing patrol.",
        ],
        "exits": [],
        "enemies": [],
    }
    out = select_opening_narration_visible_facts(public)
    patrol_hits = sum(1 for s in out if "patrol" in s.lower())
    assert patrol_hits <= 1


def test_opening_selection_keeps_social_and_actionable_when_present():
    public = {
        "id": "tavern_yard",
        "location": "Yard",
        "summary": "Busy yard.",
        "visible_facts": [
            "Stone walls enclose the muddy yard.",
            "A tavern runner waves you toward the side door.",
            "A posted notice warns of curfew at the inner gate.",
            "Ash drifts from a nearby brazier.",
            "Crates stack beside the alley mouth.",
            "Onlookers whisper when strangers pause too long.",
            "Guards scan faces at the checkpoint line.",
            "Rain slicks the cobbles near the well.",
        ],
        "exits": [],
        "enemies": [],
    }
    out = select_opening_narration_visible_facts(public)
    low = " ".join(s.lower() for s in out)
    assert "runner" in low
    assert "notice" in low or "posted" in low


def test_opening_selection_scores_activity_before_static_same_category():
    public = {
        "id": "gate",
        "location": "Gate",
        "summary": "Gate.",
        "visible_facts": [
            "Stone walls enclose the muddy gate.",
            "Banners hang over the gate arch.",
            "Guards scan faces at the checkpoint line.",
            "A posted notice warns of curfew.",
        ],
        "exits": [],
        "enemies": [],
    }

    out = select_opening_narration_visible_facts(public)

    assert out.index("Guards scan faces at the checkpoint line.") < out.index("A posted notice warns of curfew.")


def test_opening_selection_composes_environment_social_and_affordance():
    public = {
        "id": "gate",
        "location": "Gate",
        "summary": "Gate.",
        "visible_facts": [
            "Rain slicks soot-dark stone beneath the eastern gate.",
            "A guard calls for the next wagon in line.",
            "A notice board lists curfew warnings beside the arch.",
            "Smoke trails above the wall.",
        ],
        "exits": [],
        "enemies": [],
    }

    out = select_opening_narration_visible_facts(public)
    low = " ".join(s.lower() for s in out)

    assert "rain" in low or "gate" in low
    assert "guard" in low
    assert "notice" in low or "curfew" in low


def test_opening_selection_stable_ordering():
    public = {
        "id": "s",
        "location": "L",
        "summary": "S.",
        "visible_facts": [
            "Stone gate arches overhead.",
            "Crowds press toward the checkpoint.",
            "A merchant haggles with a guard.",
            "A sign lists tolls for wagons.",
            "Wind tugs at loose banners.",
        ],
        "exits": [],
        "enemies": [],
    }
    a = select_opening_narration_visible_facts(public)
    b = select_opening_narration_visible_facts(public)
    assert a == b
    # Category order A → B → C → D → E before original index tie-break
    assert a.index("Stone gate arches overhead.") < a.index("Crowds press toward the checkpoint.")


def test_opening_fact_primary_category_deterministic():
    from game.narration_visibility import _normalize_visibility_text

    n = _normalize_visibility_text
    assert opening_fact_primary_category(n("Posted notice on the gate.")) == "D"
    assert opening_fact_primary_category(n("The barkeep polishes a cup.")) == "C"
    assert opening_fact_primary_category(n("Crowds jostle near the wall.")) == "B"


def test_short_list_unchanged():
    public = {
        "id": "x",
        "location": "L",
        "summary": "S.",
        "visible_facts": ["Only one fact at the gate."],
        "exits": [],
        "enemies": [],
    }
    assert select_opening_narration_visible_facts(public) == ["Only one fact at the gate."]


def test_opening_seed_facts_beat_visible_facts():
    public = {
        "id": "seeded",
        "location": "Gate",
        "summary": "Gate.",
        "opening_seed_facts": [
            "Rain beads on soot-dark stones beneath the gate arch.",
            "A guard calls the next wagon forward.",
        ],
        "visible_facts": ["Upon closer inspection, hidden tracks reveal a smuggler route."],
        "exits": [],
        "enemies": [],
    }

    out, telemetry = select_opening_narration_visible_facts_with_telemetry(public)

    joined = " ".join(out).lower()
    assert "rain beads" in joined
    assert "guard calls" in joined
    assert "smuggler route" not in joined
    assert telemetry["opening_fact_source_used"] == "opening_seed_facts"
    assert telemetry["opening_fact_eligibility_mode"] == "explicit_source"


def test_journal_seed_facts_beat_visible_facts_when_no_opening_seed():
    public = {
        "id": "journal",
        "location": "Square",
        "summary": "Square.",
        "journal_seed_facts": ["Wind tugs at loose banners above the square."],
        "visible_facts": ["Examining the crate reveals a private cipher."],
        "exits": [],
        "enemies": [],
    }

    out, telemetry = select_opening_narration_visible_facts_with_telemetry(public)

    assert out == ["Wind tugs at loose banners above the square."]
    assert telemetry["opening_fact_source_used"] == "journal_seed_facts"


def test_lifecycle_metadata_rejects_non_opening_facts():
    public = {
        "id": "lifecycle",
        "location": "Gate",
        "summary": "Gate.",
        "visible_facts": [
            {"text": "Rain slicks the gate stones.", "metadata": {"lifecycle": "opening_seed"}},
            {"text": "The clue recovered from the crate names a culprit.", "metadata": {"lifecycle": "discovered_clue"}},
            {"text": "The player remembers a private warning.", "metadata": {"lifecycle": "pc_specific"}},
        ],
        "exits": [],
        "enemies": [],
    }

    out, telemetry = select_opening_narration_visible_facts_with_telemetry(public)

    assert out == ["Rain slicks the gate stones."]
    assert telemetry["opening_fact_source_used"] == "visible_facts_lifecycle_seed"
    assert telemetry["opening_fact_rejected_by_lifecycle_count"] == 2
    assert not is_opening_eligible_fact("The clue names a culprit.", {"lifecycle": "discovered_clue"})
    assert not is_opening_eligible_fact("The player remembers a private warning.", {"lifecycle": "pc_specific"})


def test_investigation_result_phrasing_rejected_by_form():
    public = {
        "id": "form",
        "location": "Gate",
        "summary": "Gate.",
        "visible_facts": [
            "Rain slicks the cobbles.",
            "Upon closer inspection, faint footprints lead northwest, suggesting hurried movement.",
            "Examining the notice reveals that someone has recently altered it.",
        ],
        "exits": [],
        "enemies": [],
    }

    out, telemetry = select_opening_narration_visible_facts_with_telemetry(public)

    assert out == ["Rain slicks the cobbles."]
    assert telemetry["opening_fact_eligibility_mode"] == "legacy_structural"
    assert telemetry["opening_fact_rejected_by_form_count"] == 2


def test_legacy_visible_facts_still_work_for_clean_seed_style_observations():
    public = {
        "id": "legacy",
        "location": "Gate",
        "summary": "Gate.",
        "visible_facts": [
            "Rain slicks soot-dark stone beneath the eastern gate.",
            "A guard calls for the next wagon in line.",
            "A notice board lists curfew warnings beside the arch.",
        ],
        "exits": [],
        "enemies": [],
    }

    out, telemetry = select_opening_narration_visible_facts_with_telemetry(public)

    assert len(out) == 3
    assert telemetry["opening_fact_source_used"] == "visible_facts"
    assert telemetry["opening_fact_eligibility_mode"] == "legacy_structural"
    assert telemetry["opening_fact_rejected_by_form_count"] == 0


def test_player_specific_name_rejection_uses_context_not_entity_blacklist():
    assert not is_opening_eligible_fact(
        "Galinor notices the torn parchment near the crates.",
        {"character": {"name": "Galinor"}},
    )
    assert is_opening_eligible_fact(
        "A traveler notices the torn parchment near the crates.",
        {"character": {"name": "Galinor"}},
    )
