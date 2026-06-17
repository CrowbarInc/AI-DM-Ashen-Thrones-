"""Owner tests for scene state anchor helper module.

Direct owner for ``game.final_emission_scene_state_anchor``, including gate-layer
``apply_scene_state_anchor_layer``. Gate integration and order pins remain in
``tests/test_scene_state_anchoring.py`` and ``tests/test_final_emission_gate.py``.
"""

from __future__ import annotations

import game.final_emission_gate as feg
import game.final_emission_scene_state_anchor as scene_state_anchor


def _ssa_contract(**overrides):
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
    base.update(overrides)
    return base


def test_ssa_layer_skip_reasons_direct() -> None:
    assert scene_state_anchor._skip_scene_state_anchor_layer(
        "x",
        None,
        strict_social_details=None,
    ) == "missing_contract"

    assert scene_state_anchor._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(enabled=False),
        strict_social_details=None,
    ) == "contract_disabled"

    assert scene_state_anchor._skip_scene_state_anchor_layer(
        "",
        _ssa_contract(),
        strict_social_details=None,
    ) == "empty_text"

    assert scene_state_anchor._skip_scene_state_anchor_layer(
        None,
        _ssa_contract(),
        strict_social_details=None,
    ) == "non_string_text"

    assert scene_state_anchor._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details={"used_internal_fallback": True},
    ) == "strict_social_authoritative_internal_fallback"

    assert scene_state_anchor._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details={"final_emitted_source": "neutral_reply_speaker_grounding_bridge"},
    ) == "strict_social_structured_or_bridge_source"

    assert scene_state_anchor._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": False},
    ) == "response_type_contract_failed"


def test_resolve_scene_state_anchor_contract_reads_nested_payloads() -> None:
    contract = _ssa_contract(scene_location_label="Frontier Gate")
    gm_output = {
        "narration_payload": {"scene_state_anchor_contract": contract},
    }
    resolved = scene_state_anchor._resolve_scene_state_anchor_contract(gm_output)
    assert resolved == contract


def test_repair_location_opening_prefixes_location_when_missing() -> None:
    contract = _ssa_contract(
        scene_location_label="Stone Quay",
        location_tokens=["quay", "stone"],
    )
    repaired, mode = scene_state_anchor._repair_location_opening(
        "Gulls wheel overhead.",
        contract,
    )
    assert repaired == "At Stone Quay, Gulls wheel overhead."
    assert mode == "location_rebind"


def test_repair_actor_opening_prefixes_actor_when_missing() -> None:
    contract = _ssa_contract(actor_tokens=["mara the smith"])
    repaired, mode = scene_state_anchor._repair_actor_opening(
        "The hammer rings once.",
        contract["actor_tokens"],
    )
    assert repaired == "Mara The Smith The hammer rings once."
    assert mode == "actor_rebind"


def test_merge_scene_state_anchor_meta_copies_layer_fields() -> None:
    layer_meta = scene_state_anchor._default_scene_state_anchor_meta(None, {"upstream": True})
    layer_meta["scene_state_anchor_checked"] = True
    layer_meta["scene_state_anchor_failed"] = True
    merged: dict = {}
    scene_state_anchor._merge_scene_state_anchor_meta(merged, layer_meta)
    assert merged["scene_state_anchor_checked"] is True
    assert merged["scene_state_anchor_failed"] is True
    assert merged["scene_state_anchor_upstream_debug"] == {"upstream": True}


def test_bj37_apply_scene_state_anchor_layer_passes_when_anchored() -> None:
    contract = _ssa_contract(
        scene_location_label="Stone Quay",
        location_tokens=["quay", "stone"],
    )
    text = "At Stone Quay, gulls wheel overhead."
    out_text, meta = scene_state_anchor.apply_scene_state_anchor_layer(
        text,
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
    )
    assert out_text == text
    assert meta.get("scene_state_anchor_passed") is True
    assert meta.get("scene_state_anchor_failed") is False


def test_bj37_apply_scene_state_anchor_layer_boundary_no_rewrite_on_failure() -> None:
    contract = _ssa_contract(
        scene_location_label="Stone Quay",
        location_tokens=["quay"],
        actor_tokens=["mara"],
    )
    text = "Gulls wheel overhead."
    out_text, meta = scene_state_anchor.apply_scene_state_anchor_layer(
        text,
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
    )
    assert out_text == text
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_repair_mode") is None


def test_bj85_gate_delegator_removed_stacks_call_owner_directly() -> None:
    """BJ-85: gate delegator removed; stacks call scene_state_anchor owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    assert not hasattr(feg, "_apply_scene_state_anchor_layer")
    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_scene_state_anchor_layer(" in nss_src
    assert "apply_scene_state_anchor_layer(" in ss_src
    assert "feg._apply_scene_state_anchor_layer" not in nss_src
    assert "feg._apply_scene_state_anchor_layer" not in ss_src
