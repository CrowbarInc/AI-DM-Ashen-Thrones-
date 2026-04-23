"""Composable CTIR + planner-input recipes for Objective N3 closure regression tests.

Each scenario is a small dict: ``name``, ``ctir_kwargs``, optional ``build_kwargs``,
and optional ``narrative_plan_build_extra`` merged into :func:`game.narrative_planning.build_narrative_plan`.
Keep entries minimal—this is not a scenario framework.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

from game.ctir import build_ctir

from tests.test_narrative_roles import _DIALOGUE_CONTRACT_INPUTS


def _base_narrative_anchors(**extra: Any) -> Dict[str, Any]:
    na = {
        "scene_framing": [],
        "actors_speakers": [],
        "outcomes": [],
        "uncertainty": [],
        "next_leads_affordances": [],
    }
    na.update(extra)
    return na


def _base_narrative_actors(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    return _base_narrative_anchors(actors_speakers=rows)


N3_CLOSURE_SCENARIOS: List[Dict[str, Any]] = [
    {
        "name": "grounding_location_forward",
        "ctir_kwargs": {
            "resolution": {
                "kind": "scene_transition",
                "target_scene_id": "inn",
                "state_changes": {"scene_transition_occurred": True},
            },
            "interaction": {"interaction_mode": "activity"},
            "narrative_anchors": _base_narrative_anchors(),
        },
        "build_kwargs": {
            "public_scene_slice": {
                "scene_id": "inn",
                "scene_name": "The Inn",
                "location_tokens": ["hearth", "bar", "stairs", "common room"],
            },
        },
    },
    {
        "name": "actor_forward_interaction",
        "ctir_kwargs": {
            "resolution": {"kind": "question", "social": {"npc_reply_expected": True}},
            "interaction": {"active_target_id": "npc_a", "interaction_mode": "social"},
            "narrative_anchors": _base_narrative_actors([{"id": "npc_a", "name": "A"}, {"id": "npc_b", "name": "B"}]),
        },
        "narrative_plan_build_extra": _DIALOGUE_CONTRACT_INPUTS,
    },
    {
        "name": "pressure_heavy",
        "ctir_kwargs": {
            "resolution": {
                "kind": "question",
                "social": {"npc_reply_expected": True, "reply_kind": "challenge"},
            },
            "interaction": {"active_target_id": "npc_a", "interaction_mode": "social"},
            "world": {
                "pressure": {"heat": 3, "watch": 2},
                "clocks": [{"id": "c1", "ticks": 2}],
            },
            "narrative_anchors": _base_narrative_anchors(),
        },
        "build_kwargs": {"session_interaction": {"pending_lead_ids": ["lead_1", "lead_2"]}},
        "narrative_plan_build_extra": _DIALOGUE_CONTRACT_INPUTS,
    },
    {
        "name": "hook_forward_information_rich",
        "ctir_kwargs": {
            "resolution": {
                "kind": "consequence",
                "outcome_type": "success",
                "success_state": "partial",
                "clue_id": "clue_77",
                "authoritative_outputs": {"x": True},
                "consequences": ["state shift"],
            },
            "interaction": {"interaction_mode": "activity"},
            "state_mutations": {
                "scene": {"changed_keys": ["lighting", "doors"]},
                "session": {"changed_keys": ["fatigue"]},
            },
            "narrative_anchors": _base_narrative_anchors(),
        },
    },
    {
        "name": "consequence_forward",
        "ctir_kwargs": {
            "resolution": {
                "kind": "consequence",
                "consequences": ["portcullis drops"],
                "state_changes": {"injury": True},
            },
            "interaction": {"interaction_mode": "activity"},
            "narrative_anchors": _base_narrative_anchors(),
        },
    },
    {
        "name": "mixed_richness",
        "ctir_kwargs": {
            "resolution": {
                "kind": "question",
                "clue_id": "clue_z",
                "social": {"npc_reply_expected": True},
            },
            "interaction": {"active_target_id": "npc_z", "interaction_mode": "social"},
            "world": {"pressure": {"tension": 1}},
            "narrative_anchors": _base_narrative_actors([{"id": "npc_z", "name": "Z"}]),
        },
        "build_kwargs": {
            "public_scene_slice": {"scene_id": "s1", "scene_name": "Hall", "location_tokens": ["dais", "doors"]},
            "session_interaction": {"pending_lead_ids": ["lead_x"]},
        },
        "narrative_plan_build_extra": _DIALOGUE_CONTRACT_INPUTS,
    },
    {
        "name": "sparse_but_valid",
        "ctir_kwargs": {
            "resolution": {"kind": "observe"},
            "interaction": {"interaction_mode": "activity"},
            "narrative_anchors": _base_narrative_anchors(),
        },
    },
    {
        "name": "collapse_risk_high_contrast_natural",
        "ctir_kwargs": {
            "resolution": {
                "kind": "attack",
                "outcome_type": "hit",
                "state_changes": {"hp_reduced": True},
                "consequences": ["wound"],
            },
            "interaction": {"active_target_id": "boss", "interaction_mode": "combat"},
            "narrative_anchors": _base_narrative_anchors(),
        },
        "build_kwargs": {
            "public_scene_slice": {"scene_id": "arena", "location_tokens": ["sand"]},
        },
    },
]


def build_ctir_for_n3_scenario(row: Mapping[str, Any]) -> Dict[str, Any]:
    ck = dict(row.get("ctir_kwargs") or {})
    ck.setdefault("turn_id", 1)
    ck.setdefault("scene_id", "test_scene")
    ck.setdefault("player_input", "action")
    ck.setdefault("builder_source", "tests.helpers.n3_closure_matrix")
    return build_ctir(**ck)


def build_plan_for_n3_scenario(row: Mapping[str, Any]) -> Dict[str, Any]:
    from game.narrative_planning import build_narrative_plan

    c = build_ctir_for_n3_scenario(row)
    bk = dict(row.get("build_kwargs") or {})
    extra = dict(row.get("narrative_plan_build_extra") or {})
    return build_narrative_plan(ctir=c, **bk, **extra)
