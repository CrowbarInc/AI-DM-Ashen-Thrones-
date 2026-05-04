"""Regression coverage for post-GM adoption gateway trace metadata."""
from __future__ import annotations

import pytest

import game.api as game_api
from game.api import (
    PostGmSceneUpdateEffect,
    PostGmWorldUpdatesEffect,
    _apply_post_gm_updates,
    _post_gm_adoption_classification,
    _post_gm_adoption_gateway,
    _record_post_gm_mutation_trace,
    _validate_gm_scene_update_for_legacy_adoption,
    _validate_gm_world_updates_for_legacy_adoption,
)
from game.gm import (
    GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED,
    apply_response_policy_enforcement,
)
from game.prompt_context import RESPONSE_RULE_PRIORITY
from game.storage import build_effective_scene as _storage_build_effective_scene


pytestmark = pytest.mark.integration


HIGH_RISK_BRANCHES = (
    (
        "apply_gm_scene_update_layers",
        "gm_structured_scene_update",
        ["scene_state", "player_visible_state", "hidden_state"],
    ),
    (
        "apply_gm_world_updates",
        "gm_structured_world_updates",
        ["world_state"],
    ),
    (
        "apply_social_narration_lead_supplements",
        "post_emission_social_lead_supplement",
        ["world_state", "scene_state", "player_visible_state"],
    ),
    (
        "apply_conservative_emergent_enrollment_from_gm_output",
        "post_emission_emergent_actor_enrollment",
        ["scene_state", "interaction_state"],
    ),
)


def _base_scene() -> dict:
    return {
        "scene": {
            "id": "gate",
            "visible_facts": [],
            "discoverable_clues": ["A coded mark is carved beneath the bridge rail."],
            "hidden_facts": [],
            "mode": "exploration",
            "exits": [],
            "enemies": [],
        }
    }


def test_high_risk_post_gm_branches_have_gateway_trace_contract():
    for operation, source, affected_domains in HIGH_RISK_BRANCHES:
        session: dict = {}
        classification = _post_gm_adoption_classification(operation)
        gateway = _post_gm_adoption_gateway(
            operation=operation,
            source=source,
            session=session,
            scene_id="gate",
            affected_domains=affected_domains,
            proposed_payload_summary={"payload_count": 1},
            branch_label=source,
            classification=classification,
        )
        _record_post_gm_mutation_trace(
            session,
            operation=operation,
            source=source,
            affected_domains=affected_domains,
            derived_from_model_or_post_emission=True,
            authority="authoritative",
            scene_id="gate",
            adoption_status="authoritative_adopted",
            validation_reason_codes=["audit:legacy_shape_allowed"],
            full_player_facing_text="This exact player-facing sentence must not be logged.",
            hidden_fact_payload="The sealed vault is below the shrine.",
            full_world_payload={"append_events": [{"text": "World event text."}]},
            **gateway["trace_metadata"],
        )

        trace = session["debug_traces"][-1]
        assert trace["seam"] == "post_gm_updates"
        assert trace["source"] == source
        assert trace["adoption_status"] == "authoritative_adopted"
        assert trace["risk_class"] == "high"
        assert trace["needs_gateway"] is True
        assert trace["gateway_present"] is True
        assert trace["gateway_shape_validation_enforced"] is True
        assert trace["gateway_policy_enforcement"] == "observe_only"
        assert trace["gateway_mode"] == "observe_only"
        assert trace.get("gateway_decision")
        assert trace["validation_reason_codes"] == ["audit:legacy_shape_allowed"]
        assert trace["proposed_future_owner"] == "post_gm_adoption_gateway"
        assert "This exact player-facing sentence" not in str(trace)
        assert "sealed vault" not in str(trace)
        assert "World event text." not in str(trace)


def test_low_risk_post_gm_branches_do_not_require_gateway_metadata():
    low_risk_branches = (
        ("ignore_gm_transition_proposal", "gm_transition_proposal_ignored", ["scene_state"]),
        ("detect_surfaced_clues", "post_emission_surfaced_clue_telemetry", ["player_visible_state"]),
    )
    for operation, source, affected_domains in low_risk_branches:
        session: dict = {}
        _record_post_gm_mutation_trace(
            session,
            operation=operation,
            source=source,
            affected_domains=affected_domains,
            derived_from_model_or_post_emission=True,
            authority="telemetry-only",
            scene_id="gate",
        )

        trace = session["debug_traces"][-1]
        assert trace["seam"] == "post_gm_updates"
        assert trace["source"] == source
        assert trace["risk_class"] == "low"
        assert trace["needs_gateway"] is False
        assert "gateway_present" not in trace


def test_stable_post_gm_integration_traces_include_gateway_and_hide_payloads():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "This exact player-facing sentence must not be logged.",
        "tags": [],
        "scene_update": {
            "visible_facts_add": ["A public fact."],
            "hidden_facts_add": ["The sealed vault is below the shrine."],
        },
        "activate_scene_id": "market",
        "new_scene_draft": {"title": "Proposed market"},
        "world_updates": {"append_events": [{"type": "note", "text": "World event text."}]},
        "suggested_action": None,
        "debug_notes": "",
    }

    _apply_post_gm_updates(gm, _base_scene(), session, world, combat)

    traces = session["debug_traces"]
    scene_trace = next(t for t in traces if t.get("source") == "gm_structured_scene_update")
    world_trace = next(t for t in traces if t.get("source") == "gm_structured_world_updates")
    transition_trace = next(t for t in traces if t.get("source") == "gm_transition_proposal_ignored")
    clue_trace = next(t for t in traces if t.get("source") == "post_emission_surfaced_clue_telemetry")

    for trace in (scene_trace, world_trace):
        assert trace["gateway_present"] is True
        assert trace["gateway_shape_validation_enforced"] is True
        assert trace["gateway_policy_enforcement"] == "observe_only"
        assert trace["gateway_mode"] == "observe_only"
        assert trace.get("gateway_decision")
        assert trace["proposed_future_owner"] == "post_gm_adoption_gateway"

    assert transition_trace["needs_gateway"] is False
    assert "gateway_present" not in transition_trace
    assert clue_trace["needs_gateway"] is False
    assert "gateway_present" not in clue_trace

    all_traces = str(traces)
    assert "This exact player-facing sentence" not in all_traces
    assert "The sealed vault is below the shrine." not in all_traces
    assert "World event text." not in all_traces


def test_post_gm_social_lead_supplement_valid_input_gets_validated_trace():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "Ask Lirael near the notice board about the sealed shrine.",
        "_player_facing_emission_finalized": True,
    }
    resolution = {
        "kind": "question",
        "success": True,
        "social": {"npc_id": "runner", "target_resolved": True},
    }

    _apply_post_gm_updates(gm, _base_scene(), session, world, combat, resolution=resolution)

    trace = next(t for t in session["debug_traces"] if t.get("source") == "post_emission_social_lead_supplement")
    assert trace["adoption_status"] == "authoritative_adopted"
    assert trace["gateway_present"] is True
    assert trace["gateway_decision"] == "allow_validated_legacy_social_lead_supplement"
    assert trace["gateway_shape_validation_enforced"] is True
    assert trace["gateway_policy_enforcement"] == "observe_only"
    assert trace["gateway_mode"] == "observe_only"
    assert trace["validation_reason_codes"] == ["social_lead_supplement:legacy_shape_allowed"]
    assert trace["risk_class"] == "high"
    assert trace["needs_gateway"] is True
    assert trace["narration_social_leads_count"] >= 0
    assert "Ask Lirael near the notice board" not in str(trace)
    assert "sealed shrine" not in str(trace)


def test_post_gm_social_lead_supplement_non_string_narration_rejects_without_throwing():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": {"text": "This lead text must not be adopted."},
        "_player_facing_emission_finalized": True,
    }
    resolution = {"kind": "question", "success": True}

    _, _, _, _, narration_social_leads = _apply_post_gm_updates(
        gm, _base_scene(), session, world, combat, resolution=resolution
    )

    assert narration_social_leads == []
    trace = next(t for t in session["debug_traces"] if t.get("source") == "post_emission_social_lead_supplement")
    assert trace["adoption_status"] == "rejected"
    assert trace["gateway_decision"] == "reject_unsafe_social_lead_supplement"
    assert trace["validation_reason_codes"] == ["social_lead_supplement:narration_not_string"]
    assert trace["narration_social_leads_count"] == 0
    assert "This lead text must not be adopted" not in str(trace)


def test_post_gm_social_lead_supplement_malformed_resolution_rejects_without_throwing():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "Follow the secret lead to the hidden cellar.",
        "_player_facing_emission_finalized": True,
    }

    _, _, _, _, narration_social_leads = _apply_post_gm_updates(
        gm, _base_scene(), session, world, combat, resolution="not a resolution"
    )

    assert narration_social_leads == []
    trace = next(t for t in session["debug_traces"] if t.get("source") == "post_emission_social_lead_supplement")
    assert trace["adoption_status"] == "rejected"
    assert trace["gateway_decision"] == "reject_unsafe_social_lead_supplement"
    assert trace["validation_reason_codes"] == ["social_lead_supplement:resolution_not_dict"]
    assert "secret lead" not in str(trace)
    assert "hidden cellar" not in str(trace)


def test_post_gm_social_lead_supplement_oversized_narration_rejects_without_throwing():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    oversized = "Ask Lirael near the notice board. " * 130
    gm = {
        "player_facing_text": oversized,
        "_player_facing_emission_finalized": True,
    }
    resolution = {"kind": "question", "success": True}

    _, _, _, _, narration_social_leads = _apply_post_gm_updates(
        gm, _base_scene(), session, world, combat, resolution=resolution
    )

    assert narration_social_leads == []
    trace = next(t for t in session["debug_traces"] if t.get("source") == "post_emission_social_lead_supplement")
    assert trace["adoption_status"] == "rejected"
    assert trace["gateway_decision"] == "reject_unsafe_social_lead_supplement"
    assert trace["validation_reason_codes"] == ["social_lead_supplement:narration_oversized"]
    assert trace["narration_oversized"] is True
    assert "Ask Lirael near the notice board." not in str(trace)


def test_valid_gm_world_updates_still_adopt_legacy_behavior_with_split_gateway_metadata():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "The public narration should not be traced.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": {"append_events": [{"type": "note", "text": "Raw world update event text."}]},
        "suggested_action": None,
        "debug_notes": "",
    }

    _apply_post_gm_updates(gm, _base_scene(), session, world, combat)

    assert world["event_log"] == [{"type": "gm_event", "text": "Raw world update event text."}]
    trace = next(t for t in session["debug_traces"] if t.get("source") == "gm_structured_world_updates")
    assert trace["adoption_status"] == "authoritative_adopted"
    assert trace["gateway_present"] is True
    assert trace["gateway_shape_validation_enforced"] is True
    assert trace["gateway_policy_enforcement"] == "observe_only"
    assert trace["gateway_decision"] == "allow_validated_legacy_world_updates"
    assert trace["validation_reason_codes"] == ["gm_world_updates:legacy_shape_allowed"]
    assert trace["append_events_count"] == 1
    assert "The public narration should not be traced." not in str(trace)
    assert "Raw world update event text." not in str(trace)


def test_valid_gm_world_updates_validation_produces_typed_effect():
    raw_world_updates = {"append_events": [{"type": "note", "text": "Effect event text."}]}

    validation = _validate_gm_world_updates_for_legacy_adoption(raw_world_updates)

    effect = validation["effect"]
    assert validation["allowed"] is True
    assert isinstance(effect, PostGmWorldUpdatesEffect)
    assert effect.sanitized_world_updates["append_events"] == [
        {"type": "gm_event", "text": "Effect event text."}
    ]
    assert effect.append_events_count == 1
    assert effect.update_field_count == len(effect.sanitized_world_updates)
    assert effect.validation_reason_codes == ["gm_world_updates:legacy_shape_allowed"]
    assert effect.sanitized_world_updates is not raw_world_updates


def test_gm_world_updates_mutation_uses_effect_payload_not_raw(monkeypatch):
    captured_updates: list[dict] = []

    def fake_apply_normalized_world_updates(world, normalized, *, session=None, scene_id=None):
        captured_updates.append(normalized)
        world.setdefault("event_log", []).extend(normalized.get("append_events") or [])

    monkeypatch.setattr(game_api, "apply_normalized_world_updates", fake_apply_normalized_world_updates)
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    raw_world_updates = {"append_events": [{"type": "note", "text": "Effect-applied event text."}]}
    gm = {
        "player_facing_text": "",
        "_player_facing_emission_finalized": True,
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": raw_world_updates,
        "suggested_action": None,
        "debug_notes": "",
    }

    _apply_post_gm_updates(gm, _base_scene(), session, world, combat)

    assert captured_updates[0]["append_events"] == [
        {"type": "gm_event", "text": "Effect-applied event text."}
    ]
    assert captured_updates[0] is not raw_world_updates
    assert world["event_log"] == [{"type": "gm_event", "text": "Effect-applied event text."}]


def test_invalid_gm_world_updates_reject_by_shape_validation_without_payload_trace():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "Do not trace this narration.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": {"hidden_facts": "The raw hidden world payload must not appear."},
        "suggested_action": None,
        "debug_notes": "",
    }

    _apply_post_gm_updates(gm, _base_scene(), session, world, combat)

    assert world["event_log"] == []
    trace = next(t for t in session["debug_traces"] if t.get("source") == "gm_structured_world_updates")
    assert trace["adoption_status"] == "rejected"
    assert trace["gateway_present"] is True
    assert trace["gateway_shape_validation_enforced"] is True
    assert trace["gateway_policy_enforcement"] == "observe_only"
    assert trace["gateway_decision"] == "reject_unsafe_world_updates"
    assert "gm_world_updates:unsafe_unknown_prose_key" in trace["validation_reason_codes"]
    assert "Do not trace this narration." not in str(trace)
    assert "raw hidden world payload" not in str(trace)


def test_invalid_gm_world_updates_validation_does_not_produce_effect():
    validation = _validate_gm_world_updates_for_legacy_adoption(
        {"hidden_facts": "The raw hidden world payload must not appear."}
    )

    assert validation["allowed"] is False
    assert validation["effect"] is None
    assert "gm_world_updates:unsafe_unknown_prose_key" in validation["reason_codes"]


def test_gm_structured_validators_alias_reason_codes_to_validation_reason_codes():
    world_ok = _validate_gm_world_updates_for_legacy_adoption(
        {"append_events": [{"type": "note", "text": "x"}]}
    )
    assert world_ok["reason_codes"] is world_ok["validation_reason_codes"]
    scene_ok = _validate_gm_scene_update_for_legacy_adoption({"visible_facts_add": ["a"]})
    assert scene_ok["reason_codes"] is scene_ok["validation_reason_codes"]

    world_bad = _validate_gm_world_updates_for_legacy_adoption("not a dict")
    assert world_bad["reason_codes"] is world_bad["validation_reason_codes"]
    scene_bad = _validate_gm_scene_update_for_legacy_adoption("not a dict")
    assert scene_bad["reason_codes"] is scene_bad["validation_reason_codes"]


def test_post_gm_effects_use_validation_reason_code_copies_not_validator_list_identity():
    vw = _validate_gm_world_updates_for_legacy_adoption(
        {"append_events": [{"type": "note", "text": "e"}]}
    )
    ew = vw["effect"]
    assert isinstance(ew, PostGmWorldUpdatesEffect)
    assert ew.validation_reason_codes == vw["validation_reason_codes"]
    assert ew.validation_reason_codes is not vw["validation_reason_codes"]

    vs = _validate_gm_scene_update_for_legacy_adoption({"visible_facts_add": ["x"]})
    es = vs["effect"]
    assert isinstance(es, PostGmSceneUpdateEffect)
    assert es.validation_reason_codes == vs["validation_reason_codes"]
    assert es.validation_reason_codes is not vs["validation_reason_codes"]


def test_valid_gm_scene_update_still_adopts_legacy_behavior_with_split_gateway_metadata():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    scene = _base_scene()
    gm = {
        "player_facing_text": "Narration should not be copied into trace metadata.",
        "tags": [],
        "scene_update": {
            "visible_facts_add": ["A visible legacy scene fact."],
            "hidden_facts_add": ["The raw hidden scene payload must not appear."],
        },
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }

    scene_out, _, _, _, _ = _apply_post_gm_updates(gm, scene, session, world, combat)

    assert "A visible legacy scene fact." in scene_out["scene"]["visible_facts"]
    trace = next(t for t in session["debug_traces"] if t.get("source") == "gm_structured_scene_update")
    assert trace["adoption_status"] == "authoritative_adopted"
    assert trace["gateway_present"] is True
    assert trace["gateway_shape_validation_enforced"] is True
    assert trace["gateway_policy_enforcement"] == "observe_only"
    assert trace["gateway_decision"] == "allow_validated_legacy_scene_update"
    assert trace["validation_reason_codes"] == ["gm_scene_update:legacy_shape_allowed"]
    assert trace["visible_facts_add_count"] == 1
    assert trace["hidden_facts_add_count"] == 1
    assert "Narration should not be copied" not in str(trace)
    assert "raw hidden scene payload" not in str(trace)


def test_invalid_gm_scene_update_rejects_by_shape_validation_without_payload_trace():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "This raw narration must not be logged.",
        "tags": [],
        "scene_update": {"visible_facts_add": [{"text": "Nested raw scene payload."}]},
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }

    scene_out, _, _, _, _ = _apply_post_gm_updates(gm, _base_scene(), session, world, combat)

    assert "Nested raw scene payload." not in scene_out["scene"]["visible_facts"]
    trace = next(t for t in session["debug_traces"] if t.get("source") == "gm_structured_scene_update")
    assert trace["adoption_status"] == "rejected"
    assert trace["gateway_present"] is True
    assert trace["gateway_shape_validation_enforced"] is True
    assert trace["gateway_policy_enforcement"] == "observe_only"
    assert trace["gateway_decision"] == "reject_unsafe_scene_update"
    assert "gm_scene_update:visible_facts_add:non_string_entry" in trace["validation_reason_codes"]
    assert "This raw narration must not be logged." not in str(trace)
    assert "Nested raw scene payload." not in str(trace)


def test_valid_gm_scene_update_validation_produces_typed_effect():
    raw_scene_update = {
        "visible_facts_add": ["Public fact."],
        "discoverable_clues_add": ["Clue line."],
        "hidden_facts_add": ["Hidden line."],
        "mode": "exploration",
    }
    validation = _validate_gm_scene_update_for_legacy_adoption(raw_scene_update)

    effect = validation["effect"]
    assert validation["allowed"] is True
    assert isinstance(effect, PostGmSceneUpdateEffect)
    assert effect.visible_facts_add_count == 1
    assert effect.discoverable_clues_add_count == 1
    assert effect.hidden_facts_add_count == 1
    assert effect.mode_present is True
    assert effect.validation_reason_codes == ["gm_scene_update:legacy_shape_allowed"]
    assert effect.sanitized_scene_update["visible_facts_add"] == ["Public fact."]
    assert effect.sanitized_scene_update is not raw_scene_update


def test_gm_scene_update_effect_drops_unknown_top_level_keys():
    raw_scene_update = {
        "visible_facts_add": ["Only allowed lists mutate overlay."],
        "strip_this_unknown_key": {"nested": "must not appear on effect"},
    }
    validation = _validate_gm_scene_update_for_legacy_adoption(raw_scene_update)

    assert validation["allowed"] is True
    effect = validation["effect"]
    assert isinstance(effect, PostGmSceneUpdateEffect)
    assert "strip_this_unknown_key" not in effect.sanitized_scene_update
    assert "gm_scene_update:unknown_keys_ignored" in validation["reason_codes"]


def test_invalid_gm_scene_update_validation_does_not_produce_effect():
    assert _validate_gm_scene_update_for_legacy_adoption("not a dict")["effect"] is None
    assert _validate_gm_scene_update_for_legacy_adoption(
        {"visible_facts_add": [{"text": "nested not allowed"}]}
    )["effect"] is None


def test_valid_visible_facts_add_only_mutates_overlay_via_effect():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "",
        "tags": [],
        "scene_update": {"visible_facts_add": ["Standalone visible fact."]},
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    scene_out, _, _, _, _ = _apply_post_gm_updates(gm, _base_scene(), session, world, combat)
    assert "Standalone visible fact." in scene_out["scene"]["visible_facts"]
    overlay = session["runtime_scene_overlays"]["gate"]
    assert overlay["visible_facts_add"] == ["Standalone visible fact."]
    assert overlay.get("mutations", {}).get("discoverable_clues_add") == []


def test_valid_discoverable_clues_add_only_mutates_overlay_via_effect():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "",
        "tags": [],
        "scene_update": {"discoverable_clues_add": ["A discoverable-only clue."]},
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    scene_out, _, _, _, _ = _apply_post_gm_updates(gm, _base_scene(), session, world, combat)
    assert "A discoverable-only clue." in scene_out["scene"]["discoverable_clues"]
    assert session["runtime_scene_overlays"]["gate"]["mutations"]["discoverable_clues_add"] == [
        "A discoverable-only clue."
    ]


def test_valid_hidden_facts_add_only_mutates_overlay_via_effect():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "Narration must not appear in trace.",
        "tags": [],
        "scene_update": {"hidden_facts_add": ["Hidden fact prose for overlay only."]},
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    scene_out, _, _, _, _ = _apply_post_gm_updates(gm, _base_scene(), session, world, combat)
    assert "Hidden fact prose for overlay only." in scene_out["scene"]["hidden_facts"]
    trace = next(t for t in session["debug_traces"] if t.get("source") == "gm_structured_scene_update")
    assert trace["hidden_facts_add_count"] == 1
    assert "Narration must not appear" not in str(trace)
    assert "Hidden fact prose for overlay only." not in str(trace)


def test_valid_mode_scene_update_mutates_effective_scene_via_effect():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "",
        "tags": [],
        "scene_update": {"mode": "combat"},
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    scene_out, _, _, _, _ = _apply_post_gm_updates(gm, _base_scene(), session, world, combat)
    assert scene_out["scene"]["mode"] == "combat"
    assert session["runtime_scene_overlays"]["gate"]["mutations"]["mode"] == "combat"


def test_gm_scene_update_mutation_uses_effect_payload_not_raw_dict(monkeypatch):
    captured_overlays: list[dict] = []

    def capture_build_effective_scene(canon_scene, overlay):
        captured_overlays.append(overlay)
        return _storage_build_effective_scene(canon_scene, overlay)

    monkeypatch.setattr(game_api, "build_effective_scene", capture_build_effective_scene)
    raw_scene_update = {"visible_facts_add": ["From effect path."]}
    gm = {
        "player_facing_text": "",
        "tags": [],
        "scene_update": raw_scene_update,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    _apply_post_gm_updates(gm, _base_scene(), {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}, {"event_log": []}, {"in_combat": False})

    effect = _validate_gm_scene_update_for_legacy_adoption(raw_scene_update)["effect"]
    assert isinstance(effect, PostGmSceneUpdateEffect)
    assert effect.sanitized_scene_update is not raw_scene_update
    assert captured_overlays
    last_overlay = captured_overlays[-1]
    assert last_overlay.get("visible_facts_add") == effect.sanitized_scene_update.get("visible_facts_add")


def test_apply_response_policy_enforcement_sets_semantic_policy_marker():
    pol = {k: False for k, _ in RESPONSE_RULE_PRIORITY}
    gm = apply_response_policy_enforcement(
        {"player_facing_text": "Rain."},
        response_policy=pol,
        player_text="Look.",
        scene_envelope={"scene": {"id": "gate"}},
        session={},
        world={},
        resolution={"kind": "observe"},
    )
    assert isinstance(gm.get("metadata"), dict)
    assert gm["metadata"].get(GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED) is True


def test_apply_post_gm_updates_records_semantic_policy_audit_when_marker_missing():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "Secret prose must not leak into telemetry.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    _apply_post_gm_updates(gm, _base_scene(), session, world, combat)
    audit = next(t for t in session["debug_traces"] if t.get("source") == "post_gm_adoption_semantic_policy_audit")
    assert audit["operation"] == "observe_missing_response_policy_enforcement_marker"
    assert audit["response_policy_enforcement_marker_present"] is False
    assert "post_gm_audit:response_policy_enforcement_marker_missing" in audit["validation_reason_codes"]
    assert "Secret prose" not in str(audit)


def test_apply_post_gm_updates_skips_semantic_policy_audit_when_marker_present():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "",
        "metadata": {GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED: True},
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    _apply_post_gm_updates(gm, _base_scene(), session, world, combat)
    assert not any(
        t.get("source") == "post_gm_adoption_semantic_policy_audit" for t in session.get("debug_traces", [])
    )


def test_semantic_policy_audit_does_not_break_structured_world_updates_effect_path():
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    world = {"event_log": []}
    combat = {"in_combat": False}
    gm = {
        "player_facing_text": "",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": {"append_events": [{"type": "note", "text": "Event body."}]},
        "suggested_action": None,
        "debug_notes": "",
    }
    _apply_post_gm_updates(gm, _base_scene(), session, world, combat)
    assert world["event_log"] == [{"type": "gm_event", "text": "Event body."}]
    wtrace = next(t for t in session["debug_traces"] if t.get("source") == "gm_structured_world_updates")
    assert wtrace["gateway_decision"] == "allow_validated_legacy_world_updates"
    assert "Event body." not in str(wtrace)
