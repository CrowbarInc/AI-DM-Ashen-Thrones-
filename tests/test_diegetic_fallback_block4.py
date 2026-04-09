"""Block #4: diegetic fallback/retry producers align with narration-purity expectations."""
from __future__ import annotations

from game.diegetic_fallback_narration import (
    render_global_scene_anchor_fallback,
    render_observe_perception_fallback_line,
    render_scene_momentum_diegetic_append,
    render_travel_arrival_fallback_line,
)
from game.final_emission_gate import _global_narrative_fallback_stock_line
from game.gm import enforce_scene_momentum
from game.gm_retry import _nonsocial_forced_retry_progress_line, force_terminal_retry_fallback
from game.player_facing_narration_purity import (
    build_player_facing_narration_purity_contract,
    validate_player_facing_narration_purity,
)
from game.storage import get_scene_runtime

import pytest

pytestmark = pytest.mark.unit

_STRICT_CONTRACT = build_player_facing_narration_purity_contract()


def _assert_passes_purity(text: str) -> None:
    v = validate_player_facing_narration_purity(text, _STRICT_CONTRACT)
    assert v.get("passed") is True, v


def test_observe_fallback_uses_visible_facts():
    env = {
        "scene": {
            "id": "test_gate",
            "location": "Test District",
            "visible_facts": [
                "A notice board lists new taxes and a missing patrol.",
                "Rain hammers the cobbles while the queue shuffles forward.",
            ],
        }
    }
    line = render_observe_perception_fallback_line(env, seed_key="unit|observe")
    assert line
    low = line.lower()
    assert "notice board" in low or "cobble" in low or "patrol" in low
    _assert_passes_purity(line)


def test_scene_transition_fallback_uses_destination_summary_not_prior_scene_voice():
    dest = {
        "scene": {
            "id": "stone_quay",
            "location": "Stone Quay",
            "summary": "Ropes groan against pilings while gulls wheel over slack water.",
            "visible_facts": ["Salt crusts the timbers where crates were dragged ashore."],
        }
    }
    line = render_travel_arrival_fallback_line(dest, seed_key="unit|travel")
    assert line
    low = line.lower()
    assert "rope" in low or "gull" in low or "salt" in low or "timber" in low
    assert "guard captain" not in low
    _assert_passes_purity(line)


def test_global_stock_prefers_facts_over_scene_holds():
    scene = {
        "scene": {
            "id": "x",
            "visible_facts": ["Lantern light pools on wet cobbles near the well."],
        }
    }
    alt = render_global_scene_anchor_fallback(scene, seed_key="g1")
    assert alt
    assert "scene holds" not in alt.lower()
    stock = _global_narrative_fallback_stock_line(scene, scene_id="x")
    assert "scene holds" not in stock.lower()
    assert "cobble" in stock.lower() or "lantern" in stock.lower()


def test_enforce_scene_momentum_no_scaffold_headers():
    session = {"scene_runtime": {}}
    scene = {
        "scene": {
            "id": "frontier_gate",
            "location": "Cinderwatch Gate District",
            "visible_facts": [
                "A notice board lists new taxes, curfews, and a missing patrol.",
            ],
            "exits": [{"label": "Enter Cinderwatch", "target_scene_id": "market_quarter"}],
        }
    }
    rt = get_scene_runtime(session, "frontier_gate")
    rt["momentum_exchanges_since"] = 2
    rt["momentum_next_due_in"] = 3
    gm = {"player_facing_text": "Captain Veyra's gaze stays on you.", "tags": []}
    out = enforce_scene_momentum(gm, session=session, scene_envelope=scene)
    txt = str(out.get("player_facing_text") or "")
    low = txt.lower()
    assert "consequence / opportunity" not in low
    assert "exit labeled" not in low
    assert "commit to one concrete move" not in low
    beat = render_scene_momentum_diegetic_append(scene, seed_key="frontier_gate")
    _assert_passes_purity(beat)


def test_nonsocial_forced_retry_observe_branch_concrete():
    env = {
        "scene": {
            "id": "watch_post",
            "visible_facts": ["Torchlight trembles on rain-slick merlons above the gate."],
        }
    }
    line = _nonsocial_forced_retry_progress_line(
        "I look around.",
        scene_envelope=env,
        session={},
        world={},
        resolution={"kind": "observe", "prompt": "I look around."},
    )
    low = line.lower()
    assert "next beat is yours" not in low
    assert "you weigh what you just tried" not in low
    assert "commit to one concrete move" not in low
    assert "torch" in low or "merlon" in low or "rain" in low
    _assert_passes_purity(line)


def test_force_terminal_travel_uses_arrival_not_generic_hold():
    dest = {
        "scene": {
            "id": "river_arch",
            "location": "River Arch",
            "summary": "The arch throws echoing footsteps; mist threads the river below.",
            "visible_facts": [],
        }
    }
    out = force_terminal_retry_fallback(
        session={},
        original_text="",
        failure={"failure_class": "scene_stall", "reasons": ["test"]},
        player_text="I take the riverside path.",
        scene_envelope=dest,
        world={},
        resolution={
            "kind": "scene_transition",
            "prompt": "I take the riverside path.",
            "resolved_transition": True,
        },
        base_gm={"player_facing_text": "", "tags": []},
    )
    pft = str(out.get("player_facing_text") or "")
    low = pft.lower()
    assert "scene holds" not in low
    assert "arch" in low or "river" in low or "mist" in low
    _assert_passes_purity(pft)
