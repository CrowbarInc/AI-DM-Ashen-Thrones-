from __future__ import annotations

from tests.helpers.golden_replay import (
    PROTECTED_DIALOGUE_TRACE_ROUTES,
    PROTECTED_GLOBAL_SCENE_FALLBACK_SOURCE,
    PROTECTED_NO_SCAFFOLD_TERMS,
    PROTECTED_SOCIAL_RESOLUTION_KINDS,
    PROTECTED_SOCIAL_ROUTE_KINDS,
    PROTECTED_VOCATIVE_CANONICAL_ENTRY_REASONS,
    PROTECTED_VOCATIVE_CANONICAL_ENTRY_TARGET_SOURCES,
    assert_golden_turn_observation,
    frontier_gate_branch_replay_fixture,
    validate_scenario_spine_fixture_dict,
    protected_route_expectation,
    protected_social_directed_question_expectation,
    protected_social_structural_base,
    protected_social_supplemental_structural_expectation,
    protected_social_trace_target_expectation,
    protected_social_vocative_canonical_entry_expectation,
    protected_source_expectation,
    protected_structural_expectation,
    protected_unavailable_expectation,
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


def test_protected_route_expectation_defaults_to_social_route_labels() -> None:
    assert protected_route_expectation() == {
        "one_of": {"route_kind": list(PROTECTED_SOCIAL_ROUTE_KINDS)}
    }


def test_protected_route_expectation_can_include_resolution_and_trace_labels() -> None:
    assert protected_route_expectation(
        include_resolution_kind=True,
        include_route_kind=False,
        include_trace_route=True,
    ) == {
        "one_of": {
            "resolution_kind": list(PROTECTED_SOCIAL_RESOLUTION_KINDS),
            "trace.social_contract_trace.route_selected": list(PROTECTED_DIALOGUE_TRACE_ROUTES),
        }
    }


def test_protected_source_expectation_disallows_global_scene_fallback_when_requested() -> None:
    assert protected_source_expectation() == {
        "not_equals": {"final_emitted_source": PROTECTED_GLOBAL_SCENE_FALLBACK_SOURCE}
    }
    assert protected_source_expectation(disallow_global_scene_fallback=False) == {}


def test_protected_structural_expectation_merges_route_source_and_scaffold_fragments() -> None:
    assert protected_structural_expectation(
        require_present=("final_text", "final_emitted_source"),
        allow_unavailable=("fallback_family",),
        equals={"response_type_required": "dialogue_response"},
        one_of={"trace.canonical_entry.target_source": ["spoken_vocative", "vocative"]},
        include_resolution_kind=True,
        include_trace_route=True,
        disallow_global_scene_fallback=True,
        extra_no_scaffold_terms=("Merchant",),
    ) == {
        "require_present": ["final_text", "final_emitted_source"],
        "allow_unavailable": ["fallback_family"],
        "equals": {"response_type_required": "dialogue_response"},
        "one_of": {
            "resolution_kind": list(PROTECTED_SOCIAL_RESOLUTION_KINDS),
            "route_kind": list(PROTECTED_SOCIAL_ROUTE_KINDS),
            "trace.social_contract_trace.route_selected": list(PROTECTED_DIALOGUE_TRACE_ROUTES),
            "trace.canonical_entry.target_source": ["spoken_vocative", "vocative"],
        },
        "not_equals": {"final_emitted_source": PROTECTED_GLOBAL_SCENE_FALLBACK_SOURCE},
        "text_must_not_include": ["Merchant", *PROTECTED_NO_SCAFFOLD_TERMS],
        "scaffold_leakage": False,
    }


def test_protected_structural_expectation_can_emit_only_unavailable_equals_and_trace_route() -> None:
    assert protected_structural_expectation(
        allow_unavailable=("fallback_family",),
        equals={"trace.canonical_entry.target_actor_id": "guard"},
        include_route_kind=False,
        include_trace_route=True,
        no_scaffold=False,
    ) == {
        "allow_unavailable": ["fallback_family"],
        "equals": {"trace.canonical_entry.target_actor_id": "guard"},
        "one_of": {"trace.social_contract_trace.route_selected": list(PROTECTED_DIALOGUE_TRACE_ROUTES)},
    }


def test_protected_social_directed_question_expectation_matches_full_social_lock() -> None:
    assert protected_social_directed_question_expectation("runner") == protected_social_structural_base(
        selected_speaker_id="runner",
        canonical_target_id="runner",
        require_resolution_kind=True,
        require_final_emitted_source=True,
        require_trace_target=True,
        require_trace_route=True,
        include_resolution_kind=True,
        include_trace_route=True,
        disallow_global_scene_fallback=True,
    )


def test_protected_social_trace_target_expectation_locks_canonical_actor() -> None:
    assert protected_social_trace_target_expectation("guard") == {
        "allow_unavailable": ["fallback_family"],
        "equals": {"trace.canonical_entry.target_actor_id": "guard"},
    }


def test_protected_social_vocative_canonical_entry_expectation_uses_shared_enums() -> None:
    assert protected_social_vocative_canonical_entry_expectation("guard") == {
        "allow_unavailable": ["fallback_family"],
        "equals": {"trace.canonical_entry.target_actor_id": "guard"},
        "one_of": {
            "trace.canonical_entry.target_source": list(PROTECTED_VOCATIVE_CANONICAL_ENTRY_TARGET_SOURCES),
            "trace.canonical_entry.reason": list(PROTECTED_VOCATIVE_CANONICAL_ENTRY_REASONS),
        },
    }


def test_protected_social_supplemental_structural_expectation_supports_optional_fields() -> None:
    assert protected_social_supplemental_structural_expectation() == {
        "allow_unavailable": ["fallback_family"],
    }
    assert protected_social_supplemental_structural_expectation(
        require_present=("final_emitted_source",),
        include_trace_route=True,
    ) == {
        "allow_unavailable": ["fallback_family"],
        "require_present": ["final_emitted_source"],
        "one_of": {"trace.social_contract_trace.route_selected": list(PROTECTED_DIALOGUE_TRACE_ROUTES)},
    }


def test_protected_social_structural_base_locks_speaker_target_route_and_final_source() -> None:
    assert protected_social_structural_base(
        selected_speaker_id="runner",
        canonical_target_id="runner",
        require_resolution_kind=True,
        require_final_emitted_source=True,
        require_trace_target=True,
        require_trace_route=True,
        include_resolution_kind=True,
        include_trace_route=True,
        disallow_global_scene_fallback=True,
    ) == {
        "require_present": [
            "final_text",
            "resolution_kind",
            "selected_speaker_id",
            "final_emitted_source",
            "trace.canonical_entry.target_actor_id",
            "trace.social_contract_trace.route_selected",
        ],
        "allow_unavailable": ["fallback_family"],
        "equals": {
            "selected_speaker_id": "runner",
            "trace.canonical_entry.target_actor_id": "runner",
        },
        "one_of": {
            "resolution_kind": list(PROTECTED_SOCIAL_RESOLUTION_KINDS),
            "route_kind": list(PROTECTED_SOCIAL_ROUTE_KINDS),
            "trace.social_contract_trace.route_selected": list(PROTECTED_DIALOGUE_TRACE_ROUTES),
        },
        "not_equals": {"final_emitted_source": PROTECTED_GLOBAL_SCENE_FALLBACK_SOURCE},
        "text_must_not_include": list(PROTECTED_NO_SCAFFOLD_TERMS),
        "scaffold_leakage": False,
    }


def test_protected_social_structural_base_preserves_custom_speaker_alias_fields() -> None:
    assert protected_social_structural_base(
        selected_speaker_id="runner",
        canonical_target_id="runner",
        require_present=("trace.canonical_entry.declared_alias_target_actor_id",),
        require_route_kind=False,
        equals={
            "trace.canonical_entry.declared_alias_target_actor_id": "runner",
            "trace.canonical_entry.speaker_alias_resolution_source": "manual_bundle_override",
            "dialogue_plan_valid": True,
        },
        include_route_kind=False,
    ) == {
        "require_present": [
            "final_text",
            "selected_speaker_id",
            "trace.canonical_entry.declared_alias_target_actor_id",
        ],
        "allow_unavailable": ["fallback_family"],
        "equals": {
            "selected_speaker_id": "runner",
            "trace.canonical_entry.target_actor_id": "runner",
            "trace.canonical_entry.declared_alias_target_actor_id": "runner",
            "trace.canonical_entry.speaker_alias_resolution_source": "manual_bundle_override",
            "dialogue_plan_valid": True,
        },
        "text_must_not_include": list(PROTECTED_NO_SCAFFOLD_TERMS),
        "scaffold_leakage": False,
    }


def test_protected_unavailable_expectation_preserves_field_order() -> None:
    assert protected_unavailable_expectation(
        "fallback_family",
        "trace.canonical_entry",
        "trace.social_contract_trace",
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
