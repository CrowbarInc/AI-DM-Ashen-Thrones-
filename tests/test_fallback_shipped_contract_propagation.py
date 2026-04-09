"""Shipped response_policy / context_separation contract propagation through retry fallback and final gate."""
from __future__ import annotations

import pytest

from game.campaign_state import create_fresh_session_document
from game.context_separation import build_context_separation_contract
from game.final_emission_gate import apply_final_emission_gate
from game.gm import apply_deterministic_retry_fallback, apply_response_policy_enforcement
from game.gm_retry import force_terminal_retry_fallback
from game.interaction_context import rebuild_active_scene_entities
from game.prompt_context import build_response_policy
from game.social_exchange_emission import strict_social_emission_will_apply
from game.storage import load_scene

pytestmark = pytest.mark.unit


def _shipped_cs_contract(*, kind: str = "observe", player_text: str = "I study the gate.") -> dict:
    return build_context_separation_contract(
        resolution={"kind": kind, "prompt": player_text},
        player_text=player_text,
    )


def _policy_with_context_separation(cs: dict) -> dict:
    pol = build_response_policy(
        player_text="probe",
        resolution={"kind": "observe", "prompt": "probe"},
    )
    pol = dict(pol)
    pol["context_separation"] = cs
    return pol


def _gate_session_scene_frontier():
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    st = session["scene_state"]
    st["active_entities"] = ["guard_captain", "tavern_runner", "refugee", "threadbare_watcher"]
    st.setdefault("entity_presence", {})
    st["entity_presence"].update({e: "active" for e in st["active_entities"]})
    world = {
        "npcs": [
            {"id": "guard_captain", "name": "Guard Captain", "location": "frontier_gate"},
            {"id": "tavern_runner", "name": "Runner", "location": "frontier_gate"},
        ]
    }
    scene = load_scene("frontier_gate")
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, scene, world


def _emission_cs_meta(out: dict) -> dict:
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    return {
        "resolution_source": meta.get("context_separation_contract_resolution_source"),
        "skip_reason": meta.get("context_separation_skip_reason"),
        "em_flat_source": ((out.get("metadata") or {}).get("emission_debug") or {}).get(
            "context_separation_contract_resolution_source"
        ),
    }


def test_apply_response_policy_enforcement_mirrors_policy_onto_gm() -> None:
    pol = _policy_with_context_separation(_shipped_cs_contract())
    gm = apply_response_policy_enforcement(
        {"player_facing_text": "Rain threads along the slate."},
        response_policy=pol,
        player_text="I listen.",
        scene_envelope={"scene": {"id": "s1"}},
        session={},
        world={},
        resolution={"kind": "observe", "prompt": "I listen."},
    )
    assert isinstance(gm.get("response_policy"), dict)
    assert gm["response_policy"].get("context_separation") is pol.get("context_separation")


def test_final_gate_resolves_context_separation_from_gm_response_policy() -> None:
    cs = _shipped_cs_contract()
    pol = _policy_with_context_separation(cs)
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Rain threads along the slate; the gate's iron has gone velvet with rust.",
            "response_policy": pol,
            "tags": [],
        },
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="s1",
        scene={},
        world={},
    )
    m = _emission_cs_meta(out)
    assert m["skip_reason"] != "no_shipped_contract"
    assert m["resolution_source"] == "response_policy"
    assert m["em_flat_source"] == "response_policy"


def test_final_gate_merges_session_last_turn_policy_when_gm_lacks_it() -> None:
    cs = _shipped_cs_contract()
    pol = _policy_with_context_separation(cs)
    session: dict = {"last_turn_response_policy": pol}
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Rain threads along the slate; the gate's iron has gone velvet with rust.",
            "tags": ["forced_retry_fallback", "retry_escape_hatch"],
        },
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session=session,
        scene_id="s1",
        scene={},
        world={},
    )
    m = _emission_cs_meta(out)
    assert m["skip_reason"] != "no_shipped_contract"
    assert m["resolution_source"] == "response_policy"
    assert out.get("response_policy") is pol


def test_explore_observe_resolution_stays_non_social_in_metadata() -> None:
    cs = _shipped_cs_contract(kind="observe", player_text="I scan the courtyard.")
    session = {"last_turn_response_policy": _policy_with_context_separation(cs)}
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Courtyard stones hold last night's ash in their seams.",
            "tags": ["forced_retry_fallback"],
        },
        resolution={"kind": "observe", "prompt": "I scan the courtyard."},
        session=session,
        scene_id="s1",
        scene={},
        world={},
    )
    meta = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    assert meta.get("context_separation_skip_reason") != "no_shipped_contract"
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert "speaker_contract_enforcement" not in em


def test_force_terminal_fallback_plus_enforcement_then_gate_retains_cs_contract() -> None:
    cs = _shipped_cs_contract(kind="observe", player_text="I look around.")
    pol = _policy_with_context_separation(cs)
    scene_envelope = {"scene": {"id": "s1", "summary": "A muddy yard by the gate."}}
    base = force_terminal_retry_fallback(
        session={},
        original_text="",
        failure={"failure_class": "scene_stall", "reasons": ["test"]},
        player_text="I look around.",
        scene_envelope=scene_envelope,
        world={},
        resolution={"kind": "observe", "prompt": "I look around."},
        base_gm={"player_facing_text": "x", "tags": []},
    )
    assert "forced_retry_fallback" in [str(t) for t in (base.get("tags") or [])]
    gm = apply_response_policy_enforcement(
        base,
        response_policy=pol,
        player_text="I look around.",
        scene_envelope=scene_envelope,
        session={},
        world={},
        resolution={"kind": "observe", "prompt": "I look around."},
    )
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "I look around."},
        session={},
        scene_id="s1",
        scene=scene_envelope,
        world={},
    )
    m = _emission_cs_meta(out)
    assert m["skip_reason"] != "no_shipped_contract"
    assert m["resolution_source"] == "response_policy"


def test_open_call_recovery_path_gate_merges_session_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    import game.gm_retry as gm_retry_mod

    monkeypatch.setattr(
        gm_retry_mod,
        "resolve_known_fact_before_uncertainty",
        lambda *a, **k: None,
    )
    session, scene, world = _gate_session_scene_frontier()
    cs = _shipped_cs_contract(kind="question", player_text="Anyone here know about the patrol?")
    session["last_turn_response_policy"] = _policy_with_context_separation(cs)

    resolution = {
        "kind": "question",
        "prompt": "Anyone here know about the patrol?",
        "social": {
            "social_intent_class": "open_call",
            "open_social_solicitation": True,
            "candidate_addressable_ids": ["tavern_runner", "guard_captain"],
            "candidate_addressable_count": 2,
            "target_resolved": False,
            "npc_reply_expected": False,
        },
    }
    assert strict_social_emission_will_apply(resolution, session, world, "frontier_gate") is True

    gm_fb = apply_deterministic_retry_fallback(
        {"player_facing_text": "vague", "tags": []},
        failure={"failure_class": "unresolved_question", "reasons": ["test"]},
        player_text="Anyone here know about the patrol?",
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=resolution,
    )
    tags = [str(t).lower() for t in (gm_fb.get("tags") or []) if isinstance(t, str)]
    assert "open_social_recovery" in tags
    assert gm_fb.get("response_policy") is None

    out = apply_final_emission_gate(
        gm_fb,
        resolution=resolution,
        session=session,
        scene_id="frontier_gate",
        scene=scene,
        world=world,
    )
    m = _emission_cs_meta(out)
    assert m["skip_reason"] != "no_shipped_contract"
    assert m["resolution_source"] == "response_policy"
    soc = resolution.get("social") if isinstance(resolution.get("social"), dict) else {}
    assert soc.get("social_intent_class") == "open_call"
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("open_social_recovery_used") is True
