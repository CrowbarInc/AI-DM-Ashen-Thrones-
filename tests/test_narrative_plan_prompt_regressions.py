"""Scenario regressions for CTIR → narrative_plan → prompt_context seam (Objective #2).

No GPT calls. Assertions target plan shape, payload wiring, and visibility — not prompt prose.
Baseline CTIR/narrative_plan presence tests live in ``test_prompt_context_ctir_consumption``.
"""

from __future__ import annotations

import json

import pytest

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.narration_visibility import build_narration_visibility_contract
from game.prompt_context import build_narration_context
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests


def _anchors_empty() -> dict:
    return {
        "scene_framing": [],
        "actors_speakers": [],
        "outcomes": [],
        "uncertainty": [],
        "next_leads_affordances": [],
    }


def _scene_envelope(
    scene_id: str,
    *,
    addressables: list[dict] | None = None,
) -> dict:
    inner: dict = {"id": scene_id, "visible_facts": [], "exits": [], "enemies": []}
    if addressables:
        inner["addressables"] = addressables
    return {"scene": inner}


def _world_npcs(*rows: dict) -> dict:
    return {"npcs": list(rows)}


def _addr(scene_id: str, eid: str, name: str) -> dict:
    return {
        "id": eid,
        "name": name,
        "scene_id": scene_id,
        "kind": "scene_actor",
        "addressable": True,
        "address_priority": 2,
        "aliases": [name.lower()],
    }


def _base_narration_kwargs(**overrides: object) -> dict:
    base = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": _world_npcs(),
        "session": {
            "active_scene_id": "s1",
            "turn_counter": 4,
            "visited_scene_ids": ["s0", "s1"],
            "interaction_context": {
                "active_interaction_target_id": None,
                "active_interaction_kind": None,
                "interaction_mode": "none",
            },
        },
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": _scene_envelope("s1"),
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "…",
        "resolution": {"kind": "travel", "label": "move", "action_id": "raw-walk"},
        "scene_runtime": {},
        "public_scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
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
    base.update(overrides)
    return base


def _attach_ctir(session: dict, **ctir_fields: object) -> None:
    defaults = dict(
        turn_id=4,
        scene_id="s1",
        player_input="ping",
        builder_source="tests.test_narrative_plan_prompt_regressions",
        intent={"raw_text": "ping", "labels": ["general"], "mode": "social"},
        resolution={"kind": "observe"},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors=_anchors_empty(),
    )
    defaults.update(ctir_fields)
    attach_ctir(session, ctir.build_ctir(**defaults))
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"


def _rni_kinds(plan: dict) -> list[str]:
    out: list[str] = []
    for row in plan.get("required_new_information") or []:
        if isinstance(row, dict) and row.get("kind"):
            out.append(str(row["kind"]))
    return out


def _find_rni(plan: dict, kind: str) -> dict | None:
    for row in plan.get("required_new_information") or []:
        if isinstance(row, dict) and row.get("kind") == kind:
            return row
    return None


def _allowable_ids(plan: dict) -> list[str]:
    refs = plan.get("allowable_entity_references") or []
    return sorted(str(r.get("entity_id")) for r in refs if isinstance(r, dict) and r.get("entity_id"))


def test_social_follow_up_attaches_plan_dialogue_and_interlocutor_when_visible() -> None:
    """Socially directed exchange: dialogue mode, interlocutor anchoring, structured novelty (not prose)."""
    world = _world_npcs(
        {"id": "npc_captain", "name": "Captain Rhea", "location": "s1"},
    )
    kw = _base_narration_kwargs(
        world=world,
        user_text="Captain, what word from the wall?",
        public_scene={"id": "s1", "name": "Yard", "location_tokens": ["gate", "mud"], "visible_facts": [], "exits": [], "enemies": []},
        scene=_scene_envelope("s1"),
    )
    session = dict(kw["session"])
    _attach_ctir(
        session,
        resolution={
            "kind": "question",
            "social": {"npc_reply_expected": True, "reply_kind": "answer"},
        },
        interaction={
            "active_target_id": "npc_captain",
            "interaction_mode": "social",
            "interaction_kind": "question",
            "responder_target": {"id": "npc_captain", "name": "Captain Rhea"},
        },
        narrative_anchors={
            **_anchors_empty(),
            "actors_speakers": [{"id": "npc_captain", "name": "Captain Rhea"}],
        },
    )
    ensure_narration_plan_bundle_for_manual_ctir_tests(session, {**kw, "session": session})
    try:
        ctx = build_narration_context(**{**kw, "session": session})
    finally:
        detach_ctir(session)

    plan = ctx.get("narrative_plan")
    assert isinstance(plan, dict)
    assert plan.get("narrative_mode") == "dialogue"
    assert plan["scene_anchors"].get("active_interlocutor") == "npc_captain"
    assert "resolution_kind" in _rni_kinds(plan)
    assert _allowable_ids(plan) == ["npc_captain"]
    ra = plan.get("role_allocation") or {}
    assert plan.get("narrative_mode") == plan.get("narrative_mode_contract", {}).get("mode")
    assert sum(int(ra[k]) for k in ("dialogue", "exposition", "outcome_forward", "transition")) == 100
    assert int(ra.get("dialogue", 0)) > int(ra.get("exposition", 0))


def test_consequence_turn_surfaces_atoms_without_invented_mutations_or_clues() -> None:
    """New consequence is carried structurally; prior-turn categories are not invented."""
    world = _world_npcs({"id": "npc_witness", "name": "Witness", "location": "s1"})
    kw = _base_narration_kwargs(world=world, scene=_scene_envelope("s1"))
    session = dict(kw["session"])
    _attach_ctir(
        session,
        resolution={
            "kind": "consequence",
            "consequences": ["portcullis slams shut behind you"],
        },
        interaction={"interaction_mode": "activity"},
        state_mutations={"scene": {}, "session": {}, "combat": {}, "clues_leads": {}},
        narrative_anchors={
            **_anchors_empty(),
            "actors_speakers": [{"id": "npc_witness", "name": "Witness"}],
        },
    )
    ensure_narration_plan_bundle_for_manual_ctir_tests(session, {**kw, "session": session})
    try:
        ctx = build_narration_context(**{**kw, "session": session})
    finally:
        detach_ctir(session)

    plan = ctx["narrative_plan"]
    assert plan.get("narrative_mode") not in {"consequence", "outcome", "exposition"}
    assert plan.get("narrative_mode") == plan.get("narrative_mode_contract", {}).get("mode")
    atom_row = _find_rni(plan, "consequence_atoms")
    assert atom_row is not None
    assert "portcullis slams shut behind you" in (atom_row.get("values") or [])
    assert _find_rni(plan, "surfaced_clue") is None
    assert "mutation" not in _rni_kinds(plan)
    ap = plan.get("active_pressures") or {}
    assert ap.get("interaction_pressure") == "none"
    assert not any(str(c).startswith("pressure:reply_expected") for c in (ap.get("context_codes") or []))


def test_transition_reanchors_scene_without_stale_interlocutor() -> None:
    """Arrival / relocation: transition mode, new anchors, no carried-over interlocutor from CTIR."""
    world = _world_npcs()
    kw = _base_narration_kwargs(
        world=world,
        session={
            "active_scene_id": "s_inn",
            "turn_counter": 9,
            "visited_scene_ids": ["s0", "s1", "s_inn"],
            "interaction_context": {
                "active_interaction_target_id": None,
                "active_interaction_kind": None,
                "interaction_mode": "none",
            },
        },
        scene=_scene_envelope("s_inn"),
        public_scene={
            "id": "s_inn",
            "name": "The Rusty Flagon",
            "location_tokens": ["taproom", "hearth"],
            "visible_facts": [],
            "exits": [],
            "enemies": [],
        },
    )
    session = dict(kw["session"])
    _attach_ctir(
        session,
        scene_id="s_inn",
        turn_id=9,
        resolution={
            "kind": "scene_transition",
            "target_scene_id": "s_inn",
            "state_changes": {"scene_transition_occurred": True, "arrived_at_scene": True},
        },
        interaction={"interaction_mode": "none"},
        narrative_anchors=_anchors_empty(),
    )
    ensure_narration_plan_bundle_for_manual_ctir_tests(session, {**kw, "session": session})
    try:
        ctx = build_narration_context(**{**kw, "session": session})
    finally:
        detach_ctir(session)

    plan = ctx["narrative_plan"]
    assert plan.get("narrative_mode") == "transition"
    sa = plan.get("scene_anchors") or {}
    assert sa.get("scene_id") == "s_inn"
    assert sa.get("scene_name") == "The Rusty Flagon"
    assert sa.get("location_anchors") == ["hearth", "taproom"]
    assert sa.get("active_interlocutor") is None
    assert _allowable_ids(plan) == []
    assert (ctx.get("scene") or {}).get("public", {}).get("id") == "s_inn"
    assert ctx["narrative_plan"]["scene_anchors"].get("scene_id") == "s_inn"


def test_exposition_not_default_for_structural_non_social_turns() -> None:
    """Mechanical / mutation-heavy turns stay on the six-mode contract (no legacy coarse buckets)."""
    world = _world_npcs()
    session = dict(_base_narration_kwargs(world=world)["session"])

    _attach_ctir(
        session,
        resolution={"kind": "check", "requires_check": True},
        interaction={"interaction_mode": "none"},
        intent={"raw_text": "roll", "labels": ["check"], "mode": "activity"},
        narrative_anchors=_anchors_empty(),
    )
    ensure_narration_plan_bundle_for_manual_ctir_tests(session, {**_base_narration_kwargs(world=world), "session": session})
    try:
        ctx_check = build_narration_context(**{**_base_narration_kwargs(world=world), "session": session})
    finally:
        detach_ctir(session)

    assert ctx_check["narrative_plan"]["narrative_mode"] == "continuation"
    ra_o = ctx_check["narrative_plan"]["role_allocation"]
    assert int(ra_o["exposition"]) < int(ra_o["dialogue"]) + int(ra_o["outcome_forward"])

    session2 = dict(_base_narration_kwargs(world=world)["session"])
    _attach_ctir(
        session2,
        resolution={"kind": "refinement", "label": "clarify"},
        state_mutations={"session": {"changed_keys": ["fatigue"]}, "scene": {}, "combat": {}, "clues_leads": {}},
        interaction={"interaction_mode": "none"},
        intent={"raw_text": "clarify", "labels": ["general"], "mode": "activity"},
        narrative_anchors=_anchors_empty(),
    )
    ensure_narration_plan_bundle_for_manual_ctir_tests(session2, {**_base_narration_kwargs(world=world), "session": session2})
    try:
        ctx_mut = build_narration_context(**{**_base_narration_kwargs(world=world), "session": session2})
    finally:
        detach_ctir(session2)

    assert ctx_mut["narrative_plan"]["narrative_mode"] == "continuation"

    session3 = dict(_base_narration_kwargs(world=world)["session"])
    _attach_ctir(
        session3,
        resolution={"kind": "observe"},
        interaction={"interaction_mode": "activity"},
        intent={"raw_text": "look", "labels": ["observe"], "mode": "activity"},
        narrative_anchors=_anchors_empty(),
    )
    ensure_narration_plan_bundle_for_manual_ctir_tests(session3, {**_base_narration_kwargs(world=world), "session": session3})
    try:
        ctx_obs = build_narration_context(**{**_base_narration_kwargs(world=world), "session": session3})
    finally:
        detach_ctir(session3)

    assert ctx_obs["narrative_plan"]["narrative_mode"] == "continuation"


def test_visibility_allowlist_empty_partial_and_hidden_ctir_entity() -> None:
    """Strict published_entities slice: empty universe, full visible outer boundary (OPTION A), hidden CTIR ids dropped."""
    # 1) Empty published universe → allowable stays empty even when CTIR names a target.
    world_empty = _world_npcs()
    kw0 = _base_narration_kwargs(world=world_empty, scene=_scene_envelope("s1"))
    s0 = dict(kw0["session"])
    _attach_ctir(s0, interaction={"active_target_id": "npc_phantom", "interaction_mode": "social"})
    ensure_narration_plan_bundle_for_manual_ctir_tests(s0, {**kw0, "session": s0})
    try:
        ctx0 = build_narration_context(**{**kw0, "session": s0})
    finally:
        detach_ctir(s0)
    vis0 = build_narration_visibility_contract(session=s0, scene=kw0["scene"], world=world_empty)
    assert vis0.get("visible_entity_ids") == []
    assert _allowable_ids(ctx0["narrative_plan"]) == []

    # 2) Two visible NPCs: allowable_entity_references lists the full visible roster (sorted), not only the
    #    socially focal target; focality remains on scene_anchors / mode / pressures.
    world_two = _world_npcs(
        {"id": "npc_bob", "name": "Bob", "location": "s1"},
        {"id": "npc_alice", "name": "Alice", "location": "s1"},
    )
    kw2 = _base_narration_kwargs(world=world_two, scene=_scene_envelope("s1"))
    s2 = dict(kw2["session"])
    _attach_ctir(
        s2,
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_bob", "interaction_mode": "social"},
        narrative_anchors={**_anchors_empty(), "actors_speakers": [{"id": "npc_bob", "name": "Bob"}]},
    )
    ensure_narration_plan_bundle_for_manual_ctir_tests(s2, {**kw2, "session": s2})
    try:
        ctx2 = build_narration_context(**{**kw2, "session": s2})
    finally:
        detach_ctir(s2)
    vis2 = build_narration_visibility_contract(session=s2, scene=kw2["scene"], world=world_two)
    allowed = _allowable_ids(ctx2["narrative_plan"])
    visible_sorted = sorted(str(x) for x in (vis2.get("visible_entity_ids") or []))
    assert allowed == visible_sorted == ["npc_alice", "npc_bob"]
    assert (ctx2["narrative_plan"].get("scene_anchors") or {}).get("active_interlocutor") == "npc_bob"

    # 3) CTIR references an entity not in the published universe; visible roster row still binds.
    world_one = _world_npcs({"id": "npc_alice", "name": "Alice", "location": "s1"})
    kw3 = _base_narration_kwargs(world=world_one, scene=_scene_envelope("s1"))
    s3 = dict(kw3["session"])
    _attach_ctir(
        s3,
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_shadow", "interaction_mode": "social"},
        narrative_anchors={**_anchors_empty(), "actors_speakers": [{"id": "npc_alice", "name": "Alice"}]},
    )
    ensure_narration_plan_bundle_for_manual_ctir_tests(s3, {**kw3, "session": s3})
    try:
        ctx3 = build_narration_context(**{**kw3, "session": s3})
    finally:
        detach_ctir(s3)
    assert _allowable_ids(ctx3["narrative_plan"]) == ["npc_alice"]


def test_retry_regeneration_plan_and_prompt_debug_stable() -> None:
    """Identical bounded inputs → identical plan and compact debug mirror (ordering-stable)."""
    world = _world_npcs(
        {"id": "npc_zebra", "name": "Zebra", "location": "s1"},
        {"id": "npc_alpha", "name": "Alpha", "location": "s1"},
    )
    recent = [
        {"log_meta": {"player_input": "first"}, "gm_output": {"player_facing_text": "A" * 30}},
        {"log_meta": {"player_input": "second"}, "gm_output": {"player_facing_text": "B" * 30}},
    ]
    kw = _base_narration_kwargs(
        world=world,
        user_text="What now?",
        recent_log_for_prompt=list(reversed(recent)),
        scene=_scene_envelope(
            "s1",
            addressables=[_addr("s1", "addr_one", "One"), _addr("s1", "addr_two", "Two")],
        ),
    )
    session = dict(kw["session"])
    _attach_ctir(
        session,
        resolution={"kind": "consequence", "consequences": ["alarm raised"]},
        interaction={"interaction_mode": "activity"},
        narrative_anchors={
            **_anchors_empty(),
            "actors_speakers": [
                {"id": "npc_alpha", "name": "Alpha"},
                {"id": "npc_zebra", "name": "Zebra"},
            ],
        },
    )
    ensure_narration_plan_bundle_for_manual_ctir_tests(session, {**kw, "session": session})
    try:
        ctx_a = build_narration_context(
            **{**kw, "session": session, "include_non_public_prompt_keys": True}
        )
        ctx_b = build_narration_context(
            **{**kw, "session": session, "include_non_public_prompt_keys": True}
        )
    finally:
        detach_ctir(session)

    assert ctx_a["narrative_plan"] == ctx_b["narrative_plan"]
    pd_a = (ctx_a.get("prompt_debug") or {}).get("narrative_plan") or {}
    pd_b = (ctx_b.get("prompt_debug") or {}).get("narrative_plan") or {}
    assert pd_a == pd_b
    assert pd_a.get("present") is True
    assert "scene_anchors" not in pd_a
    assert json.dumps(pd_a, sort_keys=True) == json.dumps(pd_b, sort_keys=True)
    # Ordering of allowable ids is canonical (sorted).
    assert _allowable_ids(ctx_a["narrative_plan"]) == ["addr_one", "addr_two", "npc_alpha", "npc_zebra"]
