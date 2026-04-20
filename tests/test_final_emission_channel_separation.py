"""Objective #5: public vs debug/meta channel separation at the final emission seam."""

from __future__ import annotations

from game.final_emission_meta import read_final_emission_meta_dict

from game.final_emission_gate import _finalize_emission_output
from game.final_emission_meta import (
    package_emission_channel_sidecar,
    read_debug_notes_from_turn_payload,
    read_emission_debug_lane,
    read_final_emission_meta_dict,
)
from game.state_channels import (
    assert_no_author_keys_in_player_output,
    is_debug_key,
    is_public_key,
    project_public_payload,
)


def test_finalize_emission_output_splits_public_and_debug_lanes() -> None:
    mixed = {
        "player_facing_text": "  The guard nods.  ",
        "scene_update": {"x": 1},
        "_final_emission_meta": {"final_route": "accepted", "dead_turn": {"is_dead_turn": False}},
        "stage_diff_telemetry": {"snapshots": []},
        "dead_turn": {"legacy": True},
        "reason_codes": ["rc1"],
        "lint_trace": {"n": 1},
        "author_notes": "secret",
        "internal_plan": {"p": 2},
        "debug_notes": "dbg",
    }
    out = _finalize_emission_output(
        dict(mixed),
        pre_gate_text="The guard nods.",
        fast_path=True,
        scene_emit_integrity_bundle=None,
    )
    pub = project_public_payload(out)
    assert_no_author_keys_in_player_output(pub)
    for k in pub:
        assert is_public_key(k), f"unexpected top-level key on public surface: {k!r}"
    # Objective #5 invariants: debug/meta must not leak onto the public surface.
    for forbidden in (
        "_final_emission_meta",
        "debug_notes",
        "stage_diff_telemetry",
        "dead_turn",
        "reason_codes",
        "internal_state",
        "prompt_debug",
    ):
        assert forbidden not in pub, f"public surface leaked debug/meta key: {forbidden!r}"
    assert "internal_state" in out

    internal = out.get("internal_state")
    assert isinstance(internal, dict)
    lane = internal.get("emission_debug_lane")
    assert isinstance(lane, dict)
    assert "_final_emission_meta" in lane
    assert lane.get("stage_diff_telemetry") == {"snapshots": []}
    assert "dead_turn" in lane
    assert lane.get("reason_codes") == ["rc1"]
    assert lane.get("lint_trace") == {"n": 1}
    assert lane.get("debug_notes") == "dbg"

    auth = internal.get("emission_author_lane")
    assert isinstance(auth, dict)
    assert auth.get("author_notes") == "secret"
    assert auth.get("internal_plan") == {"p": 2}

    assert read_final_emission_meta_dict(out).get("final_route") == "accepted"
    assert read_emission_debug_lane(out).get("reason_codes") == ["rc1"]


def test_package_emission_channel_sidecar_omits_empty() -> None:
    assert package_emission_channel_sidecar(debug_top_level={}, author_top_level={}) == {}
    assert package_emission_channel_sidecar(debug_top_level=None, author_top_level=None) == {}


def test_debug_key_classification_covers_fem() -> None:
    assert is_debug_key("_final_emission_meta")


def test_read_debug_notes_prefers_gm_output_debug_lane() -> None:
    payload = {
        "gm_output": {"player_facing_text": "ok"},
        "gm_output_debug": {"emission_debug_lane": {"debug_notes": "lane-dbg"}},
    }
    assert read_debug_notes_from_turn_payload(payload) == "lane-dbg"


def test_read_final_emission_meta_prefers_sidecar_over_legacy_top_level() -> None:
    """Compatibility: when both are present, sidecar wins (post-C contract)."""
    out = {
        "player_facing_text": "ok",
        "_final_emission_meta": {"final_route": "legacy_top"},
        "internal_state": {"emission_debug_lane": {"_final_emission_meta": {"final_route": "sidecar"}}},
    }
    fem = read_final_emission_meta_dict(out)
    assert fem.get("final_route") == "sidecar"
