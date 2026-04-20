"""Structural readiness proxy for Objective #2 (planning → narration seam).

This module is **not** a proof of prose quality or downstream repair elimination.
It regression-tests **first-pass structural readiness** at the
CTIR → Narrative Plan → ``build_narration_context`` payload seam: representative
turns should surface explicit mode, anchors, bounded novelty categories, visibility
handle boundaries, and role weights **before** any live model runs.

**Limitation:** The checklist is a cheap, deterministic proxy for “lower downstream
repair pressure,” not an empirical measure of GPT behavior. CTIR primacy,
derivative-only plan semantics, and strict CTIR↔plan derivation locks remain owned
by ``test_prompt_context_ctir_consumption`` and ``test_narrative_planning``; this
harness does not re-prove those contracts end-to-end.
"""

from __future__ import annotations

import json
from contextlib import contextmanager

import pytest

from game.ctir_runtime import detach_ctir
from game.narration_visibility import build_narration_visibility_contract
from game.prompt_context import build_narration_context
from tests.test_narrative_plan_prompt_regressions import (
    _allowable_ids,
    _anchors_empty,
    _attach_ctir,
    _base_narration_kwargs,
    _find_rni,
    _rni_kinds,
    _scene_envelope,
    _world_npcs,
)

_ROLE_KEYS = ("dialogue", "exposition", "outcome_forward", "transition")

# Mirrors ``_narrative_plan_prompt_debug_anchor`` public keys; catches accidental
# duplication of full plan subtrees into ``prompt_debug``.
_ALLOWED_PROMPT_DEBUG_NARRATIVE_PLAN_KEYS = frozenset(
    {
        "present",
        "build_error",
        "version",
        "narrative_mode",
        "narrative_mode_contract_valid",
        "narrative_mode_contract_validation_codes",
        "narrative_mode_contract_derivation_codes",
        "role_allocation",
        "derivation_codes",
        "derivation_code_count",
        "counts",
    }
)


def readiness_flags(ctx: dict) -> dict:
    """Small, transparent snapshot of structural signals on a narration payload."""
    plan = ctx["narrative_plan"] if isinstance(ctx.get("narrative_plan"), dict) else {}
    pd_root = ctx.get("prompt_debug") if isinstance(ctx.get("prompt_debug"), dict) else {}
    pd_np = pd_root.get("narrative_plan") if isinstance(pd_root.get("narrative_plan"), dict) else {}
    ra = plan.get("role_allocation") if isinstance(plan.get("role_allocation"), dict) else {}
    sa = plan.get("scene_anchors") if isinstance(plan.get("scene_anchors"), dict) else {}
    refs = plan.get("allowable_entity_references") if isinstance(plan.get("allowable_entity_references"), list) else []
    rni = plan.get("required_new_information") if isinstance(plan.get("required_new_information"), list) else []
    kinds = sorted({str(row.get("kind")) for row in rni if isinstance(row, dict) and row.get("kind")})
    role_sum = sum(int(ra.get(k, 0)) for k in _ROLE_KEYS) if ra else 0
    pd_keys = sorted(pd_np.keys())
    pd_json_len = len(json.dumps(pd_np, sort_keys=True)) if pd_np else 0
    return {
        "has_plan": bool(plan),
        "narrative_mode": plan.get("narrative_mode"),
        "role_allocation_sum": role_sum,
        "active_interlocutor": sa.get("active_interlocutor"),
        "scene_id": sa.get("scene_id"),
        "allowable_entity_count": len(refs),
        "required_new_information_kinds": kinds,
        "prompt_debug_narrative_plan_key_count": len(pd_keys),
        "prompt_debug_narrative_plan_json_len": pd_json_len,
        "prompt_debug_narrative_plan_present": pd_np.get("present"),
    }


def assert_prompt_debug_narrative_plan_is_compact(ctx: dict) -> None:
    pd_np = (ctx.get("prompt_debug") or {}).get("narrative_plan") or {}
    assert isinstance(pd_np, dict)
    assert set(pd_np.keys()) <= _ALLOWED_PROMPT_DEBUG_NARRATIVE_PLAN_KEYS
    if pd_np.get("present") is True:
        assert "scene_anchors" not in pd_np
        assert "required_new_information" not in pd_np
        assert "allowable_entity_references" not in pd_np
        assert "debug" not in pd_np
        # Guardrail: compact mirror stays small (counts, not duplicated rows).
        assert len(json.dumps(pd_np, sort_keys=True)) < 1200


@contextmanager
def _narration_payload(kw: dict, session: dict):
    """Build ``build_narration_context`` output while CTIR remains attached, then detach."""
    try:
        yield build_narration_context(
            **{**kw, "session": session, "include_non_public_prompt_keys": True}
        )
    finally:
        detach_ctir(session)


@pytest.mark.regression
def test_readiness_social_follow_up() -> None:
    world = _world_npcs({"id": "npc_captain", "name": "Captain Rhea", "location": "s1"})
    kw = _base_narration_kwargs(
        world=world,
        user_text="Captain, what word from the wall?",
        public_scene={
            "id": "s1",
            "name": "Yard",
            "location_tokens": ["gate", "mud"],
            "visible_facts": [],
            "exits": [],
            "enemies": [],
        },
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
    with _narration_payload(kw, session) as ctx:
        plan = ctx["narrative_plan"]
        assert plan.get("narrative_mode") == "dialogue"
        assert (plan.get("scene_anchors") or {}).get("active_interlocutor") == "npc_captain"
        assert "resolution_kind" in _rni_kinds(plan)
        assert _allowable_ids(plan) == ["npc_captain"]
        ra = plan.get("role_allocation") or {}
        assert sum(int(ra[k]) for k in _ROLE_KEYS) == 100
        assert int(ra.get("dialogue", 0)) > int(ra.get("exposition", 0))

        rf = readiness_flags(ctx)
        assert rf["has_plan"] and rf["narrative_mode"] == "dialogue"
        assert rf["role_allocation_sum"] == 100
        assert rf["active_interlocutor"] == "npc_captain"
        assert rf["allowable_entity_count"] == 1

        assert_prompt_debug_narrative_plan_is_compact(ctx)


@pytest.mark.regression
def test_readiness_consequence_state_change() -> None:
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
    with _narration_payload(kw, session) as ctx:
        plan = ctx["narrative_plan"]
        assert plan.get("narrative_mode") == "continuation"
        assert plan.get("narrative_mode") == plan.get("narrative_mode_contract", {}).get("mode")
        atom = _find_rni(plan, "consequence_atoms")
        assert atom is not None
        assert "portcullis slams shut behind you" in (atom.get("values") or [])
        assert "mutation" not in _rni_kinds(plan)

        rf = readiness_flags(ctx)
        assert "consequence_atoms" in rf["required_new_information_kinds"]
        assert_prompt_debug_narrative_plan_is_compact(ctx)


@pytest.mark.regression
def test_readiness_transition_reanchor() -> None:
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
    with _narration_payload(kw, session) as ctx:
        plan = ctx["narrative_plan"]
        assert plan.get("narrative_mode") == "transition"
        sa = plan.get("scene_anchors") or {}
        assert sa.get("scene_id") == "s_inn"
        assert sa.get("scene_name") == "The Rusty Flagon"
        assert sa.get("location_anchors") == ["hearth", "taproom"]
        assert sa.get("active_interlocutor") is None
        assert _allowable_ids(plan) == []
        assert "transition" in _rni_kinds(plan)

        rf = readiness_flags(ctx)
        assert rf["scene_id"] == "s_inn" and rf["active_interlocutor"] is None
        assert_prompt_debug_narrative_plan_is_compact(ctx)


@pytest.mark.regression
def test_readiness_plain_observation_continuation_forward() -> None:
    world = _world_npcs()
    kw = _base_narration_kwargs(world=world, scene=_scene_envelope("s1"))
    session = dict(kw["session"])
    _attach_ctir(
        session,
        resolution={"kind": "observe"},
        interaction={"interaction_mode": "activity"},
        intent={"raw_text": "look", "labels": ["observe"], "mode": "activity"},
        narrative_anchors=_anchors_empty(),
    )
    with _narration_payload(kw, session) as ctx:
        plan = ctx["narrative_plan"]
        assert plan.get("narrative_mode") == "continuation"
        assert plan.get("narrative_mode") == plan.get("narrative_mode_contract", {}).get("mode")
        assert _find_rni(plan, "consequence_atoms") is None
        assert "mutation" not in _rni_kinds(plan)
        ra = plan.get("role_allocation") or {}
        assert sum(int(ra[k]) for k in _ROLE_KEYS) == 100
        assert int(ra.get("exposition", 0)) >= int(ra.get("dialogue", 0))

        assert_prompt_debug_narrative_plan_is_compact(ctx)


@pytest.mark.regression
def test_readiness_visibility_outer_boundary_not_focality() -> None:
    world = _world_npcs(
        {"id": "npc_bob", "name": "Bob", "location": "s1"},
        {"id": "npc_alice", "name": "Alice", "location": "s1"},
    )
    kw = _base_narration_kwargs(world=world, scene=_scene_envelope("s1"))
    session = dict(kw["session"])
    _attach_ctir(
        session,
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"active_target_id": "npc_bob", "interaction_mode": "social"},
        narrative_anchors={**_anchors_empty(), "actors_speakers": [{"id": "npc_bob", "name": "Bob"}]},
    )
    with _narration_payload(kw, session) as ctx:
        plan = ctx["narrative_plan"]
        vis = build_narration_visibility_contract(session=session, scene=kw["scene"], world=world)
        visible_sorted = sorted(str(x) for x in (vis.get("visible_entity_ids") or []))
        allowed = _allowable_ids(plan)
        assert allowed == visible_sorted == ["npc_alice", "npc_bob"]
        assert len(allowed) > 1
        assert (plan.get("scene_anchors") or {}).get("active_interlocutor") == "npc_bob"
        assert plan.get("narrative_mode") == "dialogue"

        # Focality is not inferable from allowable alone (multi-handle boundary).
        assert set(allowed) != {(plan.get("scene_anchors") or {}).get("active_interlocutor")}

        assert_prompt_debug_narrative_plan_is_compact(ctx)


@pytest.mark.regression
def test_negative_no_duplicate_plan_blob_in_prompt_debug() -> None:
    """Sanity: prompt_debug must not embed full plan sections (regression guard)."""
    world = _world_npcs({"id": "npc_x", "name": "X", "location": "s1"})
    kw = _base_narration_kwargs(world=world, scene=_scene_envelope("s1"))
    session = dict(kw["session"])
    _attach_ctir(
        session,
        resolution={"kind": "observe"},
        interaction={"interaction_mode": "activity"},
        narrative_anchors=_anchors_empty(),
    )
    with _narration_payload(kw, session) as ctx:
        assert_prompt_debug_narrative_plan_is_compact(ctx)
        pd_np = (ctx.get("prompt_debug") or {}).get("narrative_plan") or {}
        assert pd_np.get("present") is True
        full_len = len(json.dumps(ctx["narrative_plan"], sort_keys=True))
        dbg_len = len(json.dumps(pd_np, sort_keys=True))
        assert full_len > dbg_len + 200


@pytest.mark.regression
def test_negative_exposition_payload_has_no_invented_consequence_atoms() -> None:
    world = _world_npcs()
    kw = _base_narration_kwargs(world=world, scene=_scene_envelope("s1"))
    session = dict(kw["session"])
    _attach_ctir(
        session,
        resolution={"kind": "observe"},
        interaction={"interaction_mode": "activity"},
        intent={"raw_text": "look", "labels": ["observe"], "mode": "activity"},
        narrative_anchors=_anchors_empty(),
    )
    with _narration_payload(kw, session) as ctx:
        assert _find_rni(ctx["narrative_plan"], "consequence_atoms") is None
