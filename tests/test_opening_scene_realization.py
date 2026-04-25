"""Tests for deterministic opening-scene realization and prompt wiring."""
from __future__ import annotations

import importlib

from game.narration_visibility import _normalize_visibility_text
from game.opening_scene_realization import (
    allowed_grounded_proper_name_norms,
    build_opening_scene_realization,
    build_opening_narration_obligations_payload,
    default_prohibited_opener_content,
    suppress_role_label_proper_name_leakage,
    validate_opening_scene_contract,
)
from game.opening_visible_fact_selection import select_opening_narration_visible_facts

build_narration_context = importlib.import_module("game.prompt_context").build_narration_context


def _vc(*names: str) -> dict:
    return {"visible_entity_names": list(names), "visible_entity_aliases": {}}


def test_contract_prefers_sensory_scene_establishing_over_notice_dump_ordering():
    public = {
        "id": "gate",
        "location": "Gate",
        "summary": "A gate.",
        "visible_facts": [
            "A posted parchment lists tolls and curfews.",
            "Rain slicks soot-dark stone; banners hang limp above the arch.",
            "Crowds press toward the checkpoint.",
        ],
        "exits": [],
        "enemies": [],
    }
    curated = select_opening_narration_visible_facts(public)
    out = build_opening_scene_realization(
        public_scene=public,
        curated_visible_fact_strings=curated,
        visibility_contract=_vc(),
    )
    anchors = out["contract"]["sensory_anchors"]
    assert anchors, anchors
    rain_norm = _normalize_visibility_text("Rain slicks soot-dark stone; banners hang limp above the arch.")
    assert _normalize_visibility_text(anchors[0]) == rain_norm


def test_role_label_leakage_suppressed_in_basis_export():
    line = "The Tavern Runner shouts offers of hot stew."
    cleaned = suppress_role_label_proper_name_leakage(line)
    assert "Tavern Runner" not in cleaned
    assert "tavern runner" in cleaned.lower()


def test_hidden_and_system_strings_not_used_as_basis_inputs():
    # Realization API never accepts gm_only slices; contract lists only public paths.
    public = {"id": "x", "location": "L", "summary": "S.", "visible_facts": ["Steam rises from a cauldron."]}
    out = build_opening_scene_realization(
        public_scene=public,
        curated_visible_fact_strings=["Steam rises from a cauldron."],
        visibility_contract=_vc(),
    )
    src = out["contract"]["source"]
    assert "hidden" not in str(src).lower()
    assert "gm_only" not in str(src).lower()


def test_premature_named_npc_blocked_when_not_grounded():
    public = {
        "id": "p",
        "location": "Square",
        "summary": "Busy.",
        "visible_facts": [
            "Lord Aldric indicates that the missing patrol could hold vital information.",
            "Rain slicks the cobbles.",
        ],
        "exits": [],
        "enemies": [],
    }
    curated = select_opening_narration_visible_facts(public)
    out = build_opening_scene_realization(
        public_scene=public,
        curated_visible_fact_strings=curated,
        visibility_contract=_vc(),
    )
    basis = out["contract"]["narration_basis_visible_facts"]
    joined = " ".join(basis).lower()
    assert "lord aldric" not in joined
    assert "vital information" not in joined


def test_grounded_honorific_allowed_when_visibility_lists_name():
    public = {
        "id": "p",
        "location": "Square",
        "summary": "Busy.",
        "visible_facts": ["Lord Aldric raises a hand in greeting."],
        "exits": [],
        "enemies": [],
    }
    out = build_opening_scene_realization(
        public_scene=public,
        curated_visible_fact_strings=["Lord Aldric raises a hand in greeting."],
        visibility_contract=_vc("Lord Aldric"),
    )
    assert "Lord Aldric" in " ".join(out["contract"]["narration_basis_visible_facts"])


def test_opening_export_stable_ordering():
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
    curated = select_opening_narration_visible_facts(public)
    a = build_opening_scene_realization(
        public_scene=public, curated_visible_fact_strings=curated, visibility_contract=_vc()
    )
    b = build_opening_scene_realization(
        public_scene=public, curated_visible_fact_strings=curated, visibility_contract=_vc()
    )
    assert a["contract"]["narration_basis_visible_facts"] == b["contract"]["narration_basis_visible_facts"]


def test_existing_opening_visible_fact_selection_preserved_under_realization():
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
    curated = select_opening_narration_visible_facts(public)
    realized = build_opening_scene_realization(
        public_scene=public,
        curated_visible_fact_strings=curated,
        visibility_contract=_vc(),
    )
    basis = realized["contract"]["narration_basis_visible_facts"]
    assert len(basis) <= len(curated)
    curated_norm_to_idx = {_normalize_visibility_text(c): i for i, c in enumerate(curated)}
    for line in basis:
        assert _normalize_visibility_text(line) in curated_norm_to_idx
    order_ix = [curated_norm_to_idx[_normalize_visibility_text(line)] for line in basis]
    assert order_ix == sorted(order_ix)
    low = " ".join(basis).lower()
    assert "runner" in low
    assert "notice" in low or "posted" in low


def test_opening_realization_rebalances_basis_from_canonical_pool():
    public = {
        "id": "gate",
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

    out = build_opening_scene_realization(
        public_scene=public,
        curated_visible_fact_strings=[
            "Rain slicks soot-dark stone beneath the eastern gate.",
            "A guard calls for the next wagon in line.",
            "A notice board lists curfew warnings beside the arch.",
        ],
        visibility_contract=_vc(),
    )
    contract = out["contract"]
    basis = " ".join(contract["narration_basis_visible_facts"]).lower()

    assert "guard" in basis
    assert "calls" in basis
    assert "next wagon" in basis or "notice" in basis or "curfew" in basis
    assert contract["opening_basis_has_actor"] is True
    assert contract["opening_basis_has_activity"] is True
    assert contract["opening_basis_has_affordance"] is True
    assert contract["opening_basis_scores"]
    assert contract["validator"]["ok"] is True


def test_opening_realization_never_reaches_past_curated_visible_facts():
    public = {
        "id": "gate",
        "location": "Gate",
        "summary": "Gate.",
        "visible_facts": [
            "Rain slicks soot-dark stone beneath the eastern gate.",
            "GM hint: the captain plans to arrest the player after sundown.",
            "Backstage: the hidden cult controls the west-road patrol.",
        ],
        "exits": [],
        "enemies": [],
    }

    out = build_opening_scene_realization(
        public_scene=public,
        curated_visible_fact_strings=["Rain slicks soot-dark stone beneath the eastern gate."],
        visibility_contract=_vc(),
    )
    basis = " ".join(out["contract"]["narration_basis_visible_facts"]).lower()

    assert "rain slicks" in basis
    assert "gm hint" not in basis
    assert "captain plans" not in basis
    assert "backstage" not in basis
    assert "hidden cult" not in basis


def test_opening_narration_obligations_payload_shape():
    off = build_opening_narration_obligations_payload(opening_mode=False)
    assert off["opening_mode"] is False
    on = build_opening_narration_obligations_payload(opening_mode=True)
    assert on["opening_mode"] is True
    assert on["opener_style"] == "scene_establishing"
    assert on["required_first_move"]["ambient_social_signal_max"] == 1


def test_briefing_role_phrases_drop_from_opening_basis():
    """Regression (OF2): pseudo-briefing lines are treated as backstage for opening basis."""
    public = {
        "id": "gate_x",
        "location": "Gate",
        "summary": "Approach.",
        "visible_facts": [
            "Rain beads on soot-dark stone; refugees queue beside muddy wagon ruts.",
            "Guard Captain indicates the western tally changed at noon without banner notice.",
            "Tavern Runner shouts wagon-clearance prices over splintering crates.",
        ],
        "exits": [],
        "enemies": [],
    }
    curated = select_opening_narration_visible_facts(public)
    out = build_opening_scene_realization(
        public_scene=public,
        curated_visible_fact_strings=curated,
        visibility_contract=_vc(),
    )
    basis = " ".join(out["contract"]["narration_basis_visible_facts"]).lower()
    assert "guard captain indicates" not in basis
    assert "tavern runner shouts" not in basis
    assert "rain" in basis


def test_validate_opening_scene_contract_detects_backstage_in_basis():
    c = {
        "narration_basis_visible_facts": ["Captain Thoran manages patrol assignments east of here."],
        "sensory_anchors": ["Captain Thoran manages patrol assignments east of here."],
    }
    v = validate_opening_scene_contract(c)
    assert v["ok"] is False
    assert "basis_contains_backstage_marker" in v["issues"]


def test_allowed_grounded_proper_name_norms_collects_aliases():
    vc = {"visible_entity_names": [], "visible_entity_aliases": {"npc1": ["Aldric of Ash", "Lord Aldric"]}}
    s = allowed_grounded_proper_name_norms(vc)
    assert "lord aldric" in s


def test_default_prohibitions_non_empty():
    assert len(default_prohibited_opener_content()) >= 3


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


def test_prompt_context_wires_opening_payload():
    public = {
        "id": "z",
        "location": "Z",
        "summary": "Z.",
        "visible_facts": ["Stone walls enclose the muddy yard.", "Wind tugs at loose banners."],
        "exits": [],
        "enemies": [],
    }
    ctx = build_narration_context(**_minimal_ctx_kwargs(public))
    assert ctx["opening_narration_obligations"]["opening_mode"] is True
    assert ctx["opening_scene_realization"]["opening_mode"] is True
    assert isinstance(ctx["opening_scene_realization"].get("contract"), dict)
    assert ctx["opening_inputs_are_curated"] is True


def test_prompt_context_opening_output_excludes_contaminated_scene_lines():
    public = {
        "id": "contaminated_gate",
        "location": "Gate",
        "summary": "Gate.",
        "visible_facts": [
            "Rain slicks soot-dark stone beneath the eastern gate.",
            "A guard calls for the next wagon in line.",
            "A notice board lists curfew warnings beside the arch.",
            "GM hint: the captain plans to arrest the player after sundown.",
            "Backstage: the hidden cult controls the west-road patrol.",
        ],
        "exits": [],
        "enemies": [],
    }
    ctx = build_narration_context(**_minimal_ctx_kwargs(public))
    exported = " ".join(
        list(ctx["narration_visibility"]["visible_facts"])
        + list(ctx["opening_scene_realization"]["contract"]["narration_basis_visible_facts"])
        + list(ctx["scene"]["public"].get("visible_facts") or [])
    ).lower()

    assert ctx["opening_inputs_are_curated"] is True
    assert "rain slicks" in exported
    assert "gm hint" not in exported
    assert "captain plans" not in exported
    assert "backstage" not in exported
    assert "hidden cult" not in exported
