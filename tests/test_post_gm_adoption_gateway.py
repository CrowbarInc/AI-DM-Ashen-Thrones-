"""Regression coverage for post-GM adoption gateway trace metadata."""
from __future__ import annotations

import pytest

from game.api import (
    _apply_post_gm_updates,
    _post_gm_adoption_classification,
    _post_gm_adoption_gateway,
    _record_post_gm_mutation_trace,
)


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
