"""BX2 — unit tests for final-emission speaker observation stamping."""
from __future__ import annotations

from copy import deepcopy

import pytest

from game.defaults import default_session, default_world
from game.final_emission_speaker_observation import (
    build_final_speaker_observation,
    stamp_final_speaker_observation,
)
from game.interaction_context import rebuild_active_scene_entities
from game.storage import load_scene
from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer

pytestmark = pytest.mark.unit

_SCENE_ID = "frontier_gate"


def _frontier_bundle(*, extra_addressables: list[dict] | None = None, extra_entities: list[str] | None = None):
    world = {"npcs": []}
    session = default_session()
    session["active_scene_id"] = _SCENE_ID
    session["interaction_context"] = {}
    scene = load_scene(_SCENE_ID)
    st = dict(session["scene_state"])
    st["active_scene_id"] = _SCENE_ID
    active = ["guard_captain", "tavern_runner", "refugee", "threadbare_watcher"]
    if extra_entities:
        for eid in extra_entities:
            if eid not in active:
                active.append(eid)
    st["active_entities"] = active
    st["entity_presence"] = {eid: "active" for eid in active}
    if extra_addressables:
        sc = deepcopy(scene.get("scene") or {})
        addr = list(sc.get("addressables") or [])
        addr.extend(extra_addressables)
        sc["addressables"] = addr
        scene = {"scene": sc, "scene_state": dict(st)}
    else:
        scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, _SCENE_ID, scene_envelope=scene)
    return session, world, scene


def _contract(primary_id: str, *, name: str | None = None) -> dict:
    return {
        "primary_speaker_id": primary_id,
        "primary_speaker_name": name or primary_id.replace("_", " ").title(),
        "primary_speaker_source": "spoken_vocative",
        "allowed_speaker_ids": [primary_id],
        "debug": {"contract_missing": False},
    }


def test_resolved_guard_captain_from_aligned_routing_and_emission() -> None:
    session, world, scene = _frontier_bundle()
    text = 'Guard Captain says, "Posted at dawn."'
    obs = build_final_speaker_observation(
        final_text=text,
        gm_output={
            "metadata": {
                "emission_debug": {
                    "speaker_selection_contract": _contract("guard_captain", name="Guard Captain"),
                }
            }
        },
        eff_resolution={"social": {"npc_id": "guard_captain", "npc_name": "Guard Captain"}},
        session=session,
        world=world,
        scene_envelope=scene,
        scene_id=_SCENE_ID,
        resolution={"prompt": "Guard, who posted that notice?"},
    )
    assert obs["status"] == "resolved"
    assert obs["canonical_speaker_id"] == "guard_captain"
    assert obs["routing_speaker_id"] == "guard_captain"


def test_resolved_gate_guard_distinct_actor() -> None:
    world = default_world()
    world["npcs"] = [{"id": "gate_guard", "name": "Gate Guard", "location": _SCENE_ID, "topics": []}]
    session, world, scene = _frontier_bundle(
        extra_addressables=[
            {
                "id": "gate_guard",
                "name": "Gate Guard",
                "scene_id": _SCENE_ID,
                "kind": "npc",
                "addressable": True,
                "address_priority": 4,
                "address_roles": ["gatekeeper"],
                "aliases": [],
            }
        ],
        extra_entities=["gate_guard"],
    )
    world = world
    text = 'Gate Guard says, "North arch."'
    obs = build_final_speaker_observation(
        final_text=text,
        gm_output={
            "metadata": {
                "emission_debug": {
                    "speaker_selection_contract": _contract("gate_guard", name="Gate Guard"),
                }
            }
        },
        eff_resolution={"social": {"npc_id": "gate_guard", "npc_name": "Gate Guard"}},
        session=session,
        world=world,
        scene_envelope=scene,
        scene_id=_SCENE_ID,
        resolution={"prompt": "Gate Guard, what is your post?"},
    )
    assert obs["status"] == "resolved"
    assert obs["canonical_speaker_id"] == "gate_guard"
    assert obs["canonical_speaker_id"] != "guard_captain"


def test_neutral_narrator_enforcement_reason() -> None:
    obs = build_final_speaker_observation(
        final_text="The rain drums on the stones.",
        gm_output={
            "metadata": {
                "emission_debug": {
                    "speaker_selection_contract": _contract("guard_captain", name="Guard Captain"),
                    "speaker_contract_enforcement": {
                        "final_reason_code": "narrator_neutral_no_allowed_speaker",
                    },
                }
            }
        },
    )
    assert obs["status"] == "neutral"
    assert obs["canonical_speaker_id"] is None


def test_unattributed_text_without_speaker_label() -> None:
    obs = build_final_speaker_observation(
        final_text="The crowd shifts uneasily.",
        gm_output={
            "metadata": {
                "emission_debug": {
                    "speaker_selection_contract": _contract("guard_captain", name="Guard Captain"),
                }
            }
        },
    )
    assert obs["status"] == "unattributed"
    assert obs["emitted_label"] is None


def test_ambiguous_bare_guard_multi_roster() -> None:
    session, world, scene = _frontier_bundle(
        extra_addressables=[
            {
                "id": "gate_sentry",
                "name": "Gate Sentry",
                "scene_id": _SCENE_ID,
                "kind": "scene_actor",
                "addressable": True,
                "address_priority": 0,
                "address_roles": ["guard", "sentry"],
                "aliases": [],
            }
        ],
        extra_entities=["gate_sentry"],
    )
    player_text = "Tell me guard, who posted that notice?"
    obs = build_final_speaker_observation(
        final_text='Guard Captain says, "Maybe."',
        gm_output={
            "metadata": {
                "emission_debug": {
                    "speaker_selection_contract": _contract("guard_captain", name="Guard Captain"),
                }
            }
        },
        eff_resolution={"social": {"npc_id": "guard_captain", "npc_name": "Guard Captain"}},
        session=session,
        world=world,
        scene_envelope=scene,
        scene_id=_SCENE_ID,
        resolution={"prompt": player_text},
    )
    assert obs["status"] == "ambiguous"
    assert obs["canonical_speaker_id"] is None
    assert obs["routing_speaker_id"] in (None, "")
    assert "guard_captain" in obs["candidates"]
    assert "gate_sentry" in obs["candidates"]


def test_unresolved_unknown_emitted_label() -> None:
    obs = build_final_speaker_observation(
        final_text='Unknown Merchant says, "I know nothing."',
        gm_output={
            "metadata": {
                "emission_debug": {
                    "speaker_selection_contract": _contract("guard_captain", name="Guard Captain"),
                }
            }
        },
        eff_resolution={"social": {"npc_id": "guard_captain", "npc_name": "Guard Captain"}},
    )
    assert obs["status"] == "unresolved"
    assert obs["canonical_speaker_id"] is None


def test_stamp_attached_at_finalize_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    from game.social_exchange_policy import reconcile_strict_social_resolution_speaker

    session, world, scene = _frontier_bundle()
    player_text = "Guard, who posted that notice?"
    resolution = reconcile_strict_social_resolution_speaker(
        {"kind": "question", "prompt": player_text, "social": {"social_intent_class": "social_exchange"}},
        session,
        world,
        _SCENE_ID,
    )
    out, _ = apply_final_emission_gate_consumer(
        {"player_facing_text": 'Guard Captain says, "At dawn."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=_SCENE_ID,
        scene=scene,
        world=world,
    )
    md = out.get("metadata") or {}
    em = md.get("emission_debug") or {}
    assert "final_speaker_observation" in em
    assert em["final_speaker_observation"]["status"] == "resolved"
