from __future__ import annotations

from tests.helpers.golden_replay import (
    PROTECTED_NO_SCAFFOLD_TERMS,
    assert_golden_turn_observation,
    frontier_gate_branch_replay_fixture,
    validate_scenario_spine_fixture_dict,
    protected_social_speaker_observation_expectation,
    protected_structural_expectation,
    render_golden_replay_markdown_report,
)


def test_frontier_gate_branch_replay_fixture_loads_validated_branch() -> None:
    fixture = frontier_gate_branch_replay_fixture("branch_social_inquiry")
    assert validate_scenario_spine_fixture_dict(fixture["spine"]) == []
    assert fixture["source_path"] == "data/validation/scenario_spines/frontier_gate_long_session.json"
    assert fixture["branch_id"] == "branch_social_inquiry"
    assert len(fixture["player_prompts"]) == 25
    assert fixture["turn_ids"][0] == "inv_01"
    assert fixture["turn_ids"][-1] == "inv_25"


def test_protected_structural_expectation_merges_consumer_fields_and_scaffold_fragment() -> None:
    assert protected_structural_expectation(
        require_present=("final_text", "final_emitted_source"),
        allow_unavailable=("fallback_family",),
        equals={"response_type_required": "dialogue_response"},
        one_of={"response_type_required": ["dialogue_response", "action_outcome"]},
        not_equals={"final_emitted_source": "global_scene_fallback"},
        extra_no_scaffold_terms=("Merchant",),
    ) == {
        "require_present": ["final_text", "final_emitted_source"],
        "allow_unavailable": ["fallback_family"],
        "equals": {"response_type_required": "dialogue_response"},
        "one_of": {"response_type_required": ["dialogue_response", "action_outcome"]},
        "not_equals": {"final_emitted_source": "global_scene_fallback"},
        "text_must_not_include": ["Merchant", *PROTECTED_NO_SCAFFOLD_TERMS],
        "scaffold_leakage": False,
    }


def test_protected_structural_expectation_can_emit_only_unavailable_and_equals() -> None:
    assert protected_structural_expectation(
        allow_unavailable=("fallback_family",),
        equals={"selected_speaker_id": "guard"},
        no_scaffold=False,
    ) == {
        "allow_unavailable": ["fallback_family"],
        "equals": {"selected_speaker_id": "guard"},
    }


def test_protected_social_speaker_observation_expectation_is_a_thin_consumer_lock() -> None:
    assert protected_social_speaker_observation_expectation("runner") == {
        "require_present": ["final_text", "selected_speaker_id"],
        "allow_unavailable": [
            "fallback_family",
            "final_emitted_source",
            "resolution_kind",
            "route_kind",
            "trace.canonical_entry",
            "trace.turn_trace",
            "trace.social_contract_trace",
        ],
        "equals": {"selected_speaker_id": "runner"},
    }


def test_protected_social_speaker_observation_expectation_allows_custom_optional_fields() -> None:
    assert protected_social_speaker_observation_expectation(
        "runner",
        allow_unavailable=("fallback_family",),
    ) == {
        "require_present": ["final_text", "selected_speaker_id"],
        "allow_unavailable": ["fallback_family"],
        "equals": {"selected_speaker_id": "runner"},
    }


def test_protected_structural_expectation_preserves_unavailable_field_order() -> None:
    assert protected_structural_expectation(
        allow_unavailable=(
            "fallback_family",
            "trace.canonical_entry",
            "trace.social_contract_trace",
        ),
        no_scaffold=False,
    ) == {
        "allow_unavailable": [
            "fallback_family",
            "trace.canonical_entry",
            "trace.social_contract_trace",
        ]
    }


def test_golden_markdown_report_renderer_is_compact_and_deterministic() -> None:
    rows = [
        {
            "scenario_id": "zeta",
            "mode": "end-to-end",
            "turn_count": 1,
            "status": "pass",
            "drift": {"status": "pass", "summary": {"exact_drift": 0, "structural_drift": 0, "semantic_drift": 0}},
            "final_emitted_source": ["generated_candidate"],
            "fallback_family": [],
            "unavailable_fields": ["fallback_family"],
            "required_invariants": ["speaker lock"],
        },
        {
            "scenario_id": "alpha",
            "mode": "schema-smoke",
            "turn_count": 3,
            "status": "pass",
            "drift_summary": "exact=0, structural=0, semantic=0",
            "final_emitted_source": ["retry_output"],
            "fallback_family": ["none"],
            "unavailable_fields": [],
            "required_invariants": ["branch ids"],
        },
    ]

    report = render_golden_replay_markdown_report(rows, title="Synthetic Report")

    assert report.index("| alpha |") < report.index("| zeta |")
    assert "Exact prose comparison is opt-in" in report
    assert "| Scenario | Mode | Turns | Status | Drift | Classifications |" in report


def test_golden_expectation_helper_supports_dotted_paths_and_debug_messages() -> None:
    turn = {
        "final_text": 'Tavern Runner says, "No names."',
        "resolution_kind": "question",
        "route_kind": "dialogue",
        "selected_speaker_id": "runner",
        "final_emitted_source": "generated_candidate",
        "fallback_family": None,
        "scaffold_leakage": False,
        "unavailable": ["fallback_family"],
        "trace": {
            "canonical_entry": {"target_actor_id": "runner"},
            "social_contract_trace": {"route_selected": "dialogue"},
        },
    }

    assert_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text", "trace.canonical_entry.target_actor_id"],
            "allow_unavailable": ["fallback_family"],
            "equals": {"trace.canonical_entry.target_actor_id": "runner"},
            "one_of": {"trace.social_contract_trace.route_selected": ["dialogue", "social"]},
            "not_equals": {"final_emitted_source": "global_scene_fallback"},
            "text_must_include": ["Tavern Runner"],
            "text_must_not_include": ["planner"],
            "scaffold_leakage": False,
        },
        debug_context="synthetic debug context",
    )

    try:
        assert_golden_turn_observation(
            turn,
            {
                "allow_unavailable": ["fallback_family"],
                "equals": {"trace.canonical_entry.target_actor_id": "gate_guard"},
            },
            debug_context="synthetic debug context",
        )
    except AssertionError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected assertion helper mismatch to fail")

    assert "trace.canonical_entry.target_actor_id" in message
    assert "gate_guard" in message
    assert "runner" in message
    assert "synthetic debug context" in message
