"""Unit tests for scene-state anchoring (Objective #8) and gate-layer SSA semantics (BH-2).

Direct ``validate_scene_state_anchoring`` contract-shape tests and SSA layer / integration
semantics extracted from ``tests/test_final_emission_gate.py``. Gate-order SSA pins remain
in the gate suite.
"""
from __future__ import annotations

import pytest

import game.final_emission_gate as feg
import game.scene_state_anchoring as ssa
from game.scene_state_anchoring import validate_scene_state_anchoring
from tests.helpers.emission_smoke_assertions import (
    apply_final_emission_gate_consumer,
    final_emission_meta_from_output,
)
from tests.helpers.strict_social_harness import runner_strict_bundle

pytestmark = pytest.mark.unit


def _apply_gate(*args, **kwargs):
    out, _ = apply_final_emission_gate_consumer(*args, **kwargs)
    return out


def _contract(**kwargs):
    base = {
        "enabled": True,
        "required_any_of": ["location", "actor", "player_action"],
        "minimum_anchor_hits": 1,
        "scene_id": "test_scene",
        "scene_location_label": None,
        "location_tokens": [],
        "actor_tokens": [],
        "player_action_tokens": [],
        "preferred_repair_order": ["actor", "player_action", "location"],
        "debug_reason": "test",
        "debug_sources": {},
    }
    base.update(kwargs)
    return base


def _ssa_contract(**overrides):
    base = {
        "enabled": True,
        "required_any_of": ["location", "actor", "player_action"],
        "minimum_anchor_hits": 1,
        "scene_id": "frontier_gate",
        "scene_location_label": None,
        "location_tokens": [],
        "actor_tokens": [],
        "player_action_tokens": [],
        "preferred_repair_order": ["actor", "player_action", "location"],
        "debug_reason": "test",
        "debug_sources": {},
    }
    base.update(overrides)
    return base


def test_validate_disabled_contract_skips_check():
    out = validate_scene_state_anchoring("anything", _contract(enabled=False))
    assert out["checked"] is False
    assert out["passed"] is True


def test_validate_invalid_contract_shape():
    out = validate_scene_state_anchoring("anything", None)
    assert out["checked"] is False
    assert out["passed"] is True
    assert "invalid_contract" in (out.get("failure_reasons") or [])


def test_validate_empty_text_failure():
    out = validate_scene_state_anchoring("", _contract())
    assert out["checked"] is True
    assert out["passed"] is False
    assert "empty_text" in (out.get("failure_reasons") or [])


def test_validate_match_kind_actor_only():
    c = _contract(actor_tokens=["keira"])
    out = validate_scene_state_anchoring("Keira taps the map once.", c)
    assert out["passed"] is True
    assert out["matched_anchor_kinds"] == ["actor"]


def test_validate_match_kind_location_only():
    c = _contract(location_tokens=["quay", "stone"])
    out = validate_scene_state_anchoring("Stone pilings line the quay.", c)
    assert out["passed"] is True
    assert "location" in out["matched_anchor_kinds"]


def test_validate_match_kind_player_action_only():
    c = _contract(player_action_tokens=["observe", "listen", "north gate"])
    out = validate_scene_state_anchoring("You listen; the north gate stays shut.", c)
    assert out["passed"] is True
    assert "player_action" in out["matched_anchor_kinds"]


def test_validate_no_anchor_match_failure_reason():
    c = _contract(actor_tokens=["zorro"])
    out = validate_scene_state_anchoring("The room is quiet.", c)
    assert out["passed"] is False
    assert "no_anchor_match" in (out.get("failure_reasons") or [])


# === BH-2: extracted from tests/test_final_emission_gate.py ===

def test_scene_state_anchor_pass_path_flags_and_matched_kinds():
    """Use location-only anchors so visibility enforcement does not replace the line (no unseen NPC names)."""
    contract = _ssa_contract(
        location_tokens=["granite", "slate"],
    )
    raw = "Granite steps wear smooth under the slate roof."
    out = _apply_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution={"kind": "observe", "prompt": "I listen for routes."},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    assert out.get("player_facing_text") == raw
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("scene_state_anchor_checked") is True
    assert meta.get("scene_state_anchor_passed") is True
    assert meta.get("scene_state_anchor_failed") is False
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_skip_reason") is None
    assert "location" in (meta.get("scene_state_anchor_matched_kinds") or [])


def test_scene_state_anchor_actor_rebind_repair_metadata():
    contract = _ssa_contract(actor_tokens=["mara the smith"])
    text, meta = feg._apply_scene_state_anchor_layer(
        "The hammer rings once.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == "The hammer rings once."
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_boundary_semantic_repair_disabled") is True


def test_scene_state_anchor_action_rebind_repair_metadata():
    contract = _ssa_contract(
        actor_tokens=[],
        player_action_tokens=["north gate", "question"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "The guards exchange a look.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == "The guards exchange a look."
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False


def test_scene_state_anchor_location_rebind_repair_metadata():
    contract = _ssa_contract(
        scene_location_label="Stone Quay",
        location_tokens=["quay", "stone"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Gulls wheel overhead.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == "Gulls wheel overhead."
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False


def test_scene_state_anchor_narrator_neutral_only_when_location_rebind_unavailable(monkeypatch):
    """C2: with anchor validation failing, boundary repair helpers are not invoked."""

    def no_location_opening(*args, **kwargs):
        return None, None

    monkeypatch.setattr(feg, "_repair_location_opening", no_location_opening)
    contract = _ssa_contract(
        scene_location_label="Ash Harbor",
        location_tokens=["harbor"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Salt stings the air.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == "Salt stings the air."
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False


def test_scene_state_anchor_unrecoverable_preserves_text_and_records_failure():
    contract = _ssa_contract(
        enabled=True,
        location_tokens=[],
        actor_tokens=[],
        player_action_tokens=[],
        scene_location_label=None,
    )
    raw = "Untethered prose with no hooks."
    text, meta = feg._apply_scene_state_anchor_layer(
        raw,
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == raw
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_repair_mode") is None
    assert meta.get("scene_state_anchor_passed") is False
    assert "no_anchor_match" in (meta.get("scene_state_anchor_failure_reasons") or [])


def test_scene_state_anchor_fast_fallback_neutral_prefers_location_rebind_over_actor_prefix():
    contract = _ssa_contract(
        scene_location_label="Frontier Gate",
        location_tokens=["frontier gate", "gate"],
        actor_tokens=["emergent lord aldric"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Several patrons exchange furtive glances.",
        gm_output={
            "scene_state_anchor_contract": contract,
            "tags": ["forced_retry_fallback", "upstream_api_fast_fallback"],
        },
        strict_social_details=None,
    )
    assert text == "Several patrons exchange furtive glances."
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False


def test_ssa_layer_skip_reasons_direct():
    assert feg._skip_scene_state_anchor_layer(
        "x",
        None,
        strict_social_details=None,
    ) == "missing_contract"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(enabled=False),
        strict_social_details=None,
    ) == "contract_disabled"

    assert feg._skip_scene_state_anchor_layer(
        "",
        _ssa_contract(),
        strict_social_details=None,
    ) == "empty_text"

    assert feg._skip_scene_state_anchor_layer(
        None,
        _ssa_contract(),
        strict_social_details=None,
    ) == "non_string_text"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details={"used_internal_fallback": True},
    ) == "strict_social_authoritative_internal_fallback"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details={"final_emitted_source": "neutral_reply_speaker_grounding_bridge"},
    ) == "strict_social_structured_or_bridge_source"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": False},
    ) == "response_type_contract_failed"


def test_validate_scene_state_anchoring_invoked_once_without_boundary_repair(monkeypatch):
    calls: list[str] = []

    def tracking_validate(t, c):
        calls.append(str(t))
        return {
            "checked": True,
            "passed": False,
            "matched_anchor_kinds": [],
            "failure_reasons": ["no_anchor_match"],
        }

    monkeypatch.setattr(feg, "validate_scene_state_anchoring", tracking_validate)
    contract = _ssa_contract(location_tokens=["beacon"])
    out = _apply_gate(
        {
            "player_facing_text": "Fog rolls in.",
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution={"kind": "observe", "prompt": "I watch."},
        session={},
        scene_id="beacon_yard",
        world={},
    )
    assert calls == ["Fog rolls in."]
    fem = final_emission_meta_from_output(out) or {}
    assert fem.get("scene_state_anchor_failed") is True
    assert fem.get("scene_state_anchor_repaired") is False


def test_gate_never_invokes_build_scene_state_anchor_contract(monkeypatch):
    def boom(*_a, **_kw):
        raise AssertionError("build_scene_state_anchor_contract must not be called from final emission gate")

    monkeypatch.setattr(ssa, "build_scene_state_anchor_contract", boom)
    out = _apply_gate(
        {
            "player_facing_text": "Stable air, cold iron.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(location_tokens=["stable"]),
        },
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert "stable" in (out.get("player_facing_text") or "").lower()


_contract_rope = _ssa_contract(location_tokens=["rope_bridge"])


@pytest.mark.parametrize(
    "attach_key,attach_payload",
    [
        ("scene_state_anchor_contract", _contract_rope),
        ("narration_payload", {"scene_state_anchor_contract": _contract_rope}),
        ("prompt_payload", {"scene_state_anchor_contract": _contract_rope}),
        ("_narration_payload", {"scene_state_anchor_contract": _contract_rope}),
        ("metadata", {"scene_state_anchor_contract": _contract_rope}),
        ("trace", {"scene_state_anchor_contract": _contract_rope}),
    ],
)
def test_contract_resolution_from_gm_output_nested_paths(attach_key, attach_payload):
    gm = {"player_facing_text": "Wind rises.", "tags": []}
    if attach_key == "scene_state_anchor_contract":
        gm["scene_state_anchor_contract"] = attach_payload
    else:
        gm[attach_key] = attach_payload
    out = _apply_gate(
        gm,
        resolution={"kind": "observe", "prompt": "I steady myself."},
        session={},
        scene_id="rope_bridge",
        world={},
    )
    assert feg._resolve_scene_state_anchor_contract(out) is not None
    fem = final_emission_meta_from_output(out) or {}
    assert fem.get("scene_state_anchor_checked") is True
    assert fem.get("scene_state_anchor_failed") is True
    assert (out.get("player_facing_text") or "").strip() == "Wind rises."


def test_strict_social_npc_line_with_actor_token_passes_without_anchor_rewrite(monkeypatch):
    session, world, sid, resolution = runner_strict_bundle()
    stub_details = {
        "used_internal_fallback": False,
        "final_emitted_source": "test_stub",
        "rejection_reasons": [],
        "deterministic_attempted": False,
        "deterministic_passed": False,
        "fallback_pool": "none",
        "fallback_kind": "none",
        "route_illegal_intercepted": False,
    }

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return 'Tavern Runner says, "East lanes."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    contract = _ssa_contract(actor_tokens=["tavern runner"])
    out = _apply_gate(
        {
            "player_facing_text": 'Tavern Runner says, "East lanes."',
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_passed") is True


def test_floating_narration_silence_line_records_anchor_failure_without_boundary_repair():
    raw = "The silence stretches for a moment."
    out = _apply_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                scene_location_label="Frontier Checkpoint",
                location_tokens=["checkpoint"],
            ),
        },
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert out.get("player_facing_text") == raw
    fem = final_emission_meta_from_output(out) or {}
    assert fem.get("scene_state_anchor_failed") is True
    assert fem.get("scene_state_anchor_repaired") is False


def test_contract_actor_only_player_action_only_location_only():
    for tokens, _kind in (
        ({"actor_tokens": ["yrsa"]}, "actor"),
        ({"player_action_tokens": ["barter check", "question"]}, "player_action"),
        ({"location_tokens": ["granary"], "scene_location_label": "Old Granary"}, "location"),
    ):
        c = _ssa_contract(**tokens)
        out = _apply_gate(
            {
                "player_facing_text": "Dust motes drift.",
                "tags": [],
                "scene_state_anchor_contract": c,
            },
            resolution={"kind": "question", "prompt": "I look."},
            session={},
            scene_id="granary_scene",
            world={},
        )
        meta = final_emission_meta_from_output(out) or {}
        assert meta.get("scene_state_anchor_failed") is True
        assert meta.get("scene_state_anchor_passed") is False


def test_scene_transition_prefers_location_when_no_actor_tokens():
    out = _apply_gate(
        {
            "player_facing_text": "The road bends without a name.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                actor_tokens=[],
                player_action_tokens=[],
                location_tokens=["crossroads"],
                scene_location_label="The Crossroads",
            ),
        },
        resolution={"kind": "observe", "prompt": "I follow the road."},
        session={},
        scene_id="crossroads",
        world={},
    )
    m = final_emission_meta_from_output(out) or {}
    assert m.get("scene_state_anchor_failed") is True
    assert m.get("scene_state_anchor_repaired") is False


def test_scene_location_label_used_when_location_tokens_sparse():
    """``scene_location_label`` drives the repair phrase; sparse ``location_tokens`` still validate the tether."""
    contract = _ssa_contract(
        location_tokens=["salt"],
        scene_location_label="Salt Docks",
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Ropes creak.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == "Ropes creak."
    assert meta.get("scene_state_anchor_failed") is True


def test_repaired_output_excludes_hidden_bucket_strings():
    gm_out = {
        "player_facing_text": "Stillness.",
        "tags": [],
        "scene_state_anchor_contract": _ssa_contract(location_tokens=["watchtower"]),
        "gm_only_hidden_facts": ["SECRET_CULT_LEADER_NAME_XYZ"],
        "metadata": {"emission_debug": {"scene_state_anchor": {"counts": {"location": 1, "actor": 0, "player_action": 0}}}},
    }
    out = _apply_gate(
        gm_out,
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="watchtower",
        world={},
    )
    assert "SECRET_CULT" not in (out.get("player_facing_text") or "")


def test_short_npc_line_grounded_by_actor_token_passes_without_rewrite():
    out = _apply_gate(
        {
            "player_facing_text": 'Kara says, "No."',
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(actor_tokens=["kara"]),
        },
        resolution={"kind": "question", "prompt": "Did they leave?"},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    assert "Kara" in (out.get("player_facing_text") or "")
    m = final_emission_meta_from_output(out) or {}
    assert m.get("scene_state_anchor_repaired") is False
    assert m.get("scene_state_anchor_passed") is True


def test_observational_follow_up_grounded_by_player_action_token():
    out = _apply_gate(
        {
            "player_facing_text": "You study the latch; rust flakes away.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                actor_tokens=[],
                player_action_tokens=["study", "latch", "investigate"],
            ),
        },
        resolution={"kind": "investigate", "prompt": "I study the latch."},
        session=None,
        scene_id="storeroom",
        world={},
    )
    m = final_emission_meta_from_output(out) or {}
    assert m.get("scene_state_anchor_passed") is True
    assert "player_action" in (m.get("scene_state_anchor_matched_kinds") or [])


def test_strict_and_non_strict_repair_sync_metadata():
    contract = _ssa_contract(location_tokens=["pier"])
    non_strict = _apply_gate(
        {
            "player_facing_text": "Fog.",
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution={"kind": "observe", "prompt": "I smell salt."},
        session={},
        scene_id="pier",
        world={},
    )
    ns = final_emission_meta_from_output(non_strict) or {}
    em_ns = (non_strict.get("metadata") or {}).get("emission_debug") or {}
    assert ns.get("scene_state_anchor_failed") is True
    assert ns.get("scene_state_anchor_repaired") is False
    assert em_ns.get("scene_state_anchor_failed") is True

    text, layer_meta = feg._apply_scene_state_anchor_layer(
        "Fog.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    merged = {}
    feg._merge_scene_state_anchor_meta(merged, layer_meta)
    assert merged.get("scene_state_anchor_failed") is True
    assert merged.get("scene_state_anchor_repaired") is False
    assert text == "Fog."
