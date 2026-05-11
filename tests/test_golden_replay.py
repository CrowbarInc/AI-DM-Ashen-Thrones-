from __future__ import annotations

import pytest

from game import storage
from game.defaults import default_scene, default_world
import game.final_emission_gate as feg
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import read_final_emission_meta_dict
from game.scenario_spine import (
    ScenarioBranch,
    ScenarioSpine,
    ScenarioTurn,
    scenario_spine_to_dict,
    validate_scenario_spine_definition,
)
from game.scenario_spine_eval import minimal_complete_transcript_turn_meta
from tests.helpers.golden_replay import (
    assert_golden_turn_observation,
    classify_golden_drift,
    final_text_has_scaffold_leakage,
    format_golden_replay_debug,
    render_golden_replay_markdown_report,
    run_golden_replay,
)
from tests.helpers.dialogue_social_plan import (
    attach_dialogue_social_plan_to_resolution,
    make_valid_dialogue_social_plan,
)
from tests.test_block_s_speaker_local_rebind_equivalence import (
    _locked_runner_contract,
    _stub_strict_social_details,
)
from tests.test_final_emission_gate import _runner_strict_bundle
from tests.test_final_emission_gate import _opening_gm_output

pytestmark = [pytest.mark.integration, pytest.mark.golden_replay]


def _gm_response(text: str, *, tags: list[str] | None = None, debug_notes: str = "") -> dict:
    return {
        "player_facing_text": text,
        "tags": list(tags or []),
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": debug_notes,
    }


def _seed_directed_runner_question_context() -> None:
    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
    scene["scene"]["location"] = "Investigator's Office"
    scene["scene"]["summary"] = "Rain taps the shutters while patrol notices curl on the desk."
    storage._save_json(storage.scene_path("scene_investigate"), scene)

    world = default_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [
                {
                    "id": "lanes",
                    "text": "They were seen near the east lanes.",
                    "clue_id": "east_lanes",
                }
            ],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    storage.save_session(session)


def _seed_runner_and_guard_context() -> None:
    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
    scene["scene"]["location"] = "Investigator's Office"
    scene["scene"]["summary"] = "A runner and a guard wait beside rain-spattered patrol maps."
    storage._save_json(storage.scene_path("scene_investigate"), scene)

    world = default_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [
                {
                    "id": "lanes",
                    "text": "They were seen near the east lanes.",
                    "clue_id": "east_lanes",
                }
            ],
        },
        {
            "id": "guard",
            "name": "Gate Guard",
            "location": "scene_investigate",
            "topics": [
                {
                    "id": "patrol",
                    "text": "The guard saw fresh mud by the north arch.",
                    "clue_id": "north_arch_mud",
                }
            ],
        },
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    storage.save_session(session)


def _seed_runner_continuity_context() -> None:
    _seed_runner_and_guard_context()
    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    session.setdefault("scene_state", {})["current_interlocutor"] = "runner"
    storage.save_session(session)


def _seed_tavern_patrol_lead_context() -> None:
    tavern = default_scene("tavern")
    tavern["scene"]["id"] = "tavern"
    tavern["scene"]["location"] = "Rain Barrel Tavern"
    tavern["scene"]["summary"] = "A crowded tavern hums around a runner with news of the missing patrol."
    tavern["scene"]["exits"] = [{"label": "Path to the old milestone", "target_scene_id": "old_milestone"}]
    storage._save_json(storage.scene_path("tavern"), tavern)

    milestone = default_scene("old_milestone")
    milestone["scene"]["id"] = "old_milestone"
    milestone["scene"]["location"] = "Old Milestone"
    storage._save_json(storage.scene_path("old_milestone"), milestone)

    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "tavern",
            "topics": [
                {
                    "id": "patrol_milestone",
                    "text": "The patrol never came back from the old milestone.",
                    "clue_id": "c_patrol_milestone",
                    "leads_to_scene": "old_milestone",
                }
            ],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session["active_scene_id"] = "tavern"
    session["visited_scene_ids"] = ["tavern"]
    storage.save_session(session)


def _seed_scene_object_investigation_context() -> None:
    scene = default_scene("scene_investigate")
    scene["scene"]["id"] = "scene_investigate"
    scene["scene"]["location"] = "Investigator's Office"
    scene["scene"]["summary"] = "A rain-damp office holds patrol maps, a desk, and a public notice board."
    scene["scene"]["visible_facts"] = [
        "A notice board carries a posting about the missing patrol.",
        "An ink-stained desk is crowded with patrol maps.",
    ]
    scene["scene"]["interactables"] = [
        {
            "id": "notice_board",
            "label": "Notice board",
            "aliases": ["notice", "posting about the missing patrol"],
            "type": "investigate",
            "reveals_clue": "notice_patrol_details",
        }
    ]
    scene["scene"]["discoverable_clues"] = [
        {"id": "notice_patrol_details", "text": "The missing patrol was last seen below the east ridge."}
    ]
    storage._save_json(storage.scene_path("scene_investigate"), scene)

    world = default_world()
    world["npcs"] = []
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session["active_scene_id"] = "scene_investigate"
    session["visited_scene_ids"] = ["scene_investigate"]
    storage.save_session(session)


def _seed_spine_three_branch_context() -> None:
    _seed_runner_and_guard_context()
    scene = storage.load_scene("scene_investigate")
    scene["scene"]["visible_facts"] = [
        "A runner waits by the desk with road gossip.",
        "A gate guard studies muddy patrol marks.",
        "A notice board carries a posting about the missing patrol.",
    ]
    scene["scene"]["interactables"] = [
        {
            "id": "notice_board",
            "label": "Notice board",
            "aliases": ["notice", "posting about the missing patrol"],
            "type": "investigate",
            "reveals_clue": "notice_patrol_details",
        }
    ]
    scene["scene"]["discoverable_clues"] = [
        {"id": "notice_patrol_details", "text": "The missing patrol was last seen below the east ridge."}
    ]
    storage._save_json(storage.scene_path("scene_investigate"), scene)


def test_golden_expectation_helper_supports_dotted_paths_and_debug_messages():
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

    with pytest.raises(AssertionError) as exc:
        assert_golden_turn_observation(
            turn,
            {
                "allow_unavailable": ["fallback_family"],
                "equals": {"trace.canonical_entry.target_actor_id": "gate_guard"},
            },
            debug_context="synthetic debug context",
        )
    message = str(exc.value)
    assert "trace.canonical_entry.target_actor_id" in message
    assert "gate_guard" in message
    assert "runner" in message
    assert "synthetic debug context" in message


def test_golden_drift_classifier_buckets_exact_structural_and_semantic_drift():
    observed = {
        "final_text": "Planner: the guard shrugs.",
        "route_kind": "action",
        "selected_speaker_id": "guard",
        "final_emitted_source": "global_scene_fallback",
        "fallback_family": "gate_terminal_repair",
        "scaffold_leakage": True,
        "unavailable": [],
        "trace": {"canonical_entry": {"target_actor_id": "guard"}},
    }
    expectation = {
        "exact_text": "The runner answers.",
        "equals": {
            "route_kind": "dialogue",
            "selected_speaker_id": "runner",
            "trace.canonical_entry.target_actor_id": "runner",
        },
        "not_equals": {"final_emitted_source": "global_scene_fallback"},
        "text_must_not_include": ["Planner"],
        "scaffold_leakage": False,
    }

    drift = classify_golden_drift(observed, expectation)

    assert drift["status"] == "fail"
    assert drift["summary"]["exact_drift"] == 1
    assert drift["summary"]["structural_drift"] == 4
    assert drift["summary"]["semantic_drift"] == 2


def test_golden_markdown_report_renderer_is_compact_and_deterministic():
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
    assert "| Scenario | Mode | Turns | Status | Drift |" in report


def test_golden_replay_directed_npc_question_structural_invariants(tmp_path, monkeypatch):
    captured_prompts: list[list[dict]] = []

    def _fake_call_gpt(messages):
        captured_prompts.append(messages)
        return _gm_response('Tavern Runner grimaces. "I heard east-road talk, but no names."')

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)

        result = run_golden_replay(
            scenario_id="directed_npc_question",
            turns=["Runner, who attacked the patrol?"],
            tmp_path=tmp_path,
            monkeypatch=monkeypatch,
            setup_fn=_seed_directed_runner_question_context,
        )

    assert captured_prompts
    assert result["turn_count"] == 1
    turn = result["turns"][0]
    directed_npc_question_expectation = {
        "require_present": [
            "final_text",
            "resolution_kind",
            "route_kind",
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
            "resolution_kind": ["question", "social", "social_exchange", "dialogue"],
            "route_kind": ["social", "question", "social_engine", "dialogue"],
            "trace.social_contract_trace.route_selected": ["social", "dialogue"],
        },
        "not_equals": {"final_emitted_source": "global_scene_fallback"},
        "text_must_not_include": ["planner", "router", "validator", "adjudication", "scaffold"],
        "scaffold_leakage": False,
    }
    assert_golden_turn_observation(
        turn,
        directed_npc_question_expectation,
        debug_context=format_golden_replay_debug(result),
    )


def test_golden_replay_vocative_override_after_prior_continuity_structural_invariants(tmp_path, monkeypatch):
    responses = iter(
        [
            _gm_response('Tavern Runner says, "I saw the patrol turn toward the east lanes."'),
            _gm_response('Gate Guard says, "I saw fresh mud by the north arch."'),
        ]
    )

    def _fake_call_gpt(_messages):
        return next(responses)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)

        result = run_golden_replay(
            scenario_id="vocative_override_after_prior_continuity",
            turns=[
                "Runner, where did the patrol go?",
                "Guard, what did you see?",
            ],
            tmp_path=tmp_path,
            monkeypatch=monkeypatch,
            setup_fn=_seed_runner_and_guard_context,
        )

    assert result["turn_count"] == 2
    turn = result["turns"][1]
    debug_context = format_golden_replay_debug(result)
    assert_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text", "selected_speaker_id"],
            "allow_unavailable": [
                "fallback_family",
                "final_emitted_source",
                "route_kind",
                "trace.canonical_entry",
                "trace.turn_trace",
                "trace.social_contract_trace",
            ],
            "equals": {"selected_speaker_id": "guard"},
            "text_must_not_include": ["planner", "router", "validator", "adjudication", "scaffold"],
            "scaffold_leakage": False,
        },
        debug_context=debug_context,
    )
    if "route_kind" not in turn.get("unavailable", []):
        assert_golden_turn_observation(
            turn,
            {"allow_unavailable": ["fallback_family"], "one_of": {"route_kind": ["social", "question", "social_engine", "dialogue"]}},
            debug_context=debug_context,
        )
    canonical_entry = (turn.get("trace") or {}).get("canonical_entry") or {}
    if canonical_entry:
        assert_golden_turn_observation(
            turn,
            {
                "allow_unavailable": ["fallback_family"],
                "equals": {"trace.canonical_entry.target_actor_id": "guard"},
                "one_of": {
                    "trace.canonical_entry.target_source": ["spoken_vocative", "vocative"],
                    "trace.canonical_entry.reason": [
                        "spoken_vocative_address",
                        "spoken_vocative_resolved_to_addressable_actor",
                        "explicit_spoken_vocative_overrode_continuity",
                        "spoken_vocative_overrode_continuity",
                    ],
                },
            },
            debug_context=debug_context,
        )
    social_contract_trace = (turn.get("trace") or {}).get("social_contract_trace") or {}
    if social_contract_trace.get("route_selected") is not None:
        assert_golden_turn_observation(
            turn,
            {
                "allow_unavailable": ["fallback_family"],
                "one_of": {"trace.social_contract_trace.route_selected": ["social", "dialogue"]},
            },
            debug_context=debug_context,
        )


def test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants(tmp_path, monkeypatch):
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response('Merchant says, "I know nothing about that."'))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)

        result = run_golden_replay(
            scenario_id="wrong_speaker_strict_social_emission",
            turns=["Who attacked the patrol?"],
            tmp_path=tmp_path,
            monkeypatch=monkeypatch,
            setup_fn=_seed_runner_continuity_context,
        )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    debug_context = format_golden_replay_debug(result)
    assert_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text", "selected_speaker_id"],
            "allow_unavailable": ["fallback_family", "final_emitted_source"],
            "equals": {"selected_speaker_id": "runner"},
            "text_must_not_include": ["Merchant", "planner", "router", "validator", "adjudication", "scaffold"],
            "scaffold_leakage": False,
        },
        debug_context=debug_context,
    )
    if "final_emitted_source" not in turn.get("unavailable", []):
        assert_golden_turn_observation(
            turn,
            {"allow_unavailable": ["fallback_family"], "require_present": ["final_emitted_source"]},
            debug_context=debug_context,
        )


def test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants(monkeypatch):
    session, world, scene_id, resolution = _runner_strict_bundle()
    attach_dialogue_social_plan_to_resolution(
        resolution,
        make_valid_dialogue_social_plan(
            speaker_id="tavern_runner",
            speaker_name="Tavern Runner",
            dialogue_intent="question",
            allowed_pregate_speaker_labels=["Ragged stranger"],
            speaker_alias_resolution_source="manual_bundle_override",
        ),
    )
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(_locked_runner_contract()))

    pre_gate_line = 'Ragged stranger says, "No names, only rumors."'

    def _fake_build(_candidate_text, *, resolution, tags, session, scene_id, world):
        return pre_gate_line, _stub_strict_social_details()

    monkeypatch.setattr(feg, "build_final_strict_social_response", _fake_build)

    out = apply_final_emission_gate(
        {"player_facing_text": pre_gate_line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=scene_id,
        world=world,
    )

    final_text = str(out.get("player_facing_text") or "")
    meta = read_final_emission_meta_dict(out) or {}
    turn = {
        "final_text": final_text,
        "selected_speaker_id": (resolution.get("social") or {}).get("npc_id"),
        "final_emitted_source": meta.get("final_emitted_source"),
        "fallback_family": meta.get("fallback_family_used") or meta.get("realization_fallback_family"),
        "scaffold_leakage": final_text_has_scaffold_leakage(final_text),
        "unavailable": ["fallback_family"],
        "trace": {
            "canonical_entry": {
                "target_actor_id": (resolution.get("social") or {}).get("npc_id"),
                "declared_alias_target_actor_id": (resolution.get("social") or {}).get("npc_id"),
                "allowed_pregate_speaker_labels": ["Ragged stranger"],
                "speaker_alias_resolution_source": "manual_bundle_override",
            }
        },
        "dialogue_plan_valid": meta.get("dialogue_plan_valid"),
    }

    assert_golden_turn_observation(
        turn,
        {
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
            "text_must_not_include": ["planner", "router", "validator", "adjudication", "scaffold"],
            "scaffold_leakage": False,
        },
        debug_context=f"meta={meta!r}; final_text={final_text!r}",
    )


def test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants(tmp_path, monkeypatch):
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("The scene pauses without offering anything concrete."))
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)

        result = run_golden_replay(
            scenario_id="thin_answer_action_outcome_final_emission",
            turns=["I examine the notice board; does it show where the missing patrol went?"],
            tmp_path=tmp_path,
            monkeypatch=monkeypatch,
            setup_fn=_seed_scene_object_investigation_context,
        )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    low = str(turn.get("final_text") or "").lower()
    debug_context = format_golden_replay_debug(result)
    assert_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text", "final_emitted_source"],
            "allow_unavailable": [
                "fallback_family",
                "selected_speaker_id",
                "trace.canonical_entry",
                "trace.social_contract_trace",
            ],
            "equals": {
                "response_type_required": "action_outcome",
                "response_type_repair_used": True,
            },
            "not_equals": {"final_emitted_source": "global_scene_fallback"},
            "text_must_not_include": [
                "scene pauses",
                "nothing concrete",
                "no name comes clear",
                "planner",
                "router",
                "validator",
                "adjudication",
                "scaffold",
            ],
            "scaffold_leakage": False,
        },
        debug_context=debug_context,
    )
    assert "patrol" in low or "east ridge" in low or "notice" in low, debug_context


def test_golden_replay_sanitizer_scaffold_leakage_structural_invariants(tmp_path, monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response("Planner: route via router. Validator: unresolved scaffold."),
        )
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)

        result = run_golden_replay(
            scenario_id="sanitizer_scaffold_leakage",
            turns=["Where should I start?"],
            tmp_path=tmp_path,
            monkeypatch=monkeypatch,
            setup_fn=_seed_scene_object_investigation_context,
        )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    assert_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text"],
            "allow_unavailable": [
                "fallback_family",
                "final_emitted_source",
                "selected_speaker_id",
                "trace.canonical_entry",
                "trace.social_contract_trace",
            ],
            "text_must_not_include": ["Planner", "planner", "router", "Validator", "validator", "scaffold"],
            "scaffold_leakage": False,
        },
        debug_context=format_golden_replay_debug(result),
    )
    if "final_emitted_source" not in turn.get("unavailable", []):
        assert_golden_turn_observation(
            turn,
            {
                "allow_unavailable": [
                    "fallback_family",
                    "selected_speaker_id",
                    "trace.canonical_entry",
                    "trace.social_contract_trace",
                ],
                "require_present": ["final_emitted_source"],
            },
            debug_context=format_golden_replay_debug(result),
        )


def test_golden_direct_seam_opening_fallback_path_structural_invariants():
    gm_output = _opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    final_text = str(out.get("player_facing_text") or "")
    meta = read_final_emission_meta_dict(out) or {}
    turn = {
        "final_text": final_text,
        "final_emitted_source": meta.get("final_emitted_source"),
        "response_type_required": meta.get("response_type_required"),
        "response_type_repair_used": meta.get("response_type_repair_used"),
        "response_type_repair_kind": meta.get("response_type_repair_kind"),
        "opening_recovered_via_fallback": meta.get("opening_recovered_via_fallback"),
        "opening_fallback_authorship_source": meta.get("opening_fallback_authorship_source"),
        "fallback_family": meta.get("fallback_family_used") or meta.get("realization_fallback_family"),
        "fallback_temporal_frame": meta.get("fallback_temporal_frame"),
        "scaffold_leakage": final_text_has_scaffold_leakage(final_text),
        "unavailable": [],
    }

    assert_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text", "final_emitted_source", "fallback_family"],
            "equals": {
                "final_emitted_source": "opening_deterministic_fallback",
                "response_type_required": "scene_opening",
                "response_type_repair_used": True,
                "response_type_repair_kind": "opening_deterministic_fallback",
                "opening_recovered_via_fallback": True,
                "fallback_family": "scene_opening",
                "fallback_temporal_frame": "first_impression",
            },
            "one_of": {
                "opening_fallback_authorship_source": [
                    "upstream_prepared_opening_fallback",
                    "compatibility_local",
                ]
            },
            "text_must_not_include": ["planner", "router", "validator", "adjudication", "scaffold"],
            "scaffold_leakage": False,
        },
        debug_context=f"meta={meta!r}; final_text={final_text!r}",
    )


def test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants(tmp_path, monkeypatch):
    responses = iter(
        [
            _gm_response(
                'Tavern Runner says, "The patrol never came back from the old milestone beyond the east road."'
            ),
            _gm_response('Tavern Runner says, "Last reliable sign was the old milestone."'),
        ]
    )

    def _fake_call_gpt(_messages):
        return next(responses)

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)

        result = run_golden_replay(
            scenario_id="lead_followup_with_dialogue_lock",
            turns=[
                "Tavern Runner, what happened to the patrol?",
                "Runner, where were they last seen?",
            ],
            tmp_path=tmp_path,
            monkeypatch=monkeypatch,
            setup_fn=_seed_tavern_patrol_lead_context,
        )

    assert result["turn_count"] == 2
    turn = result["turns"][1]
    debug_context = format_golden_replay_debug(result)
    assert_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text", "selected_speaker_id", "final_emitted_source"],
            "allow_unavailable": ["fallback_family"],
            "equals": {"selected_speaker_id": "tavern_runner"},
            "one_of": {
                "route_kind": ["social", "question", "social_engine", "dialogue"],
                "trace.social_contract_trace.route_selected": ["social", "dialogue"],
            },
            "text_must_not_include": ["planner", "router", "validator", "adjudication", "scaffold"],
            "scaffold_leakage": False,
        },
        debug_context=debug_context,
    )
    canonical_entry = (turn.get("trace") or {}).get("canonical_entry") or {}
    if canonical_entry:
        assert_golden_turn_observation(
            turn,
            {
                "allow_unavailable": ["fallback_family"],
                "equals": {"trace.canonical_entry.target_actor_id": "tavern_runner"},
            },
            debug_context=debug_context,
        )


def test_golden_replay_scenario_spine_three_branch_structural_smoke(tmp_path, monkeypatch):
    spine = ScenarioSpine(
        spine_id="golden_smoke_frontier_gate",
        title="Golden smoke three branch spine",
        smoke_only=True,
        fixed_start_state={"scene_id": "scene_investigate"},
        branches=(
            ScenarioBranch(
                branch_id="branch_runner_question",
                label="Ask the runner",
                turns=(ScenarioTurn(turn_id="runner_ask", player_prompt="Runner, who attacked the patrol?"),),
            ),
            ScenarioBranch(
                branch_id="branch_guard_question",
                label="Ask the guard",
                turns=(ScenarioTurn(turn_id="guard_ask", player_prompt="Guard, what did you see?"),),
            ),
            ScenarioBranch(
                branch_id="branch_notice_check",
                label="Check the notice",
                turns=(
                    ScenarioTurn(
                        turn_id="notice_check",
                        player_prompt="I examine the notice board; does it show where the missing patrol went?",
                    ),
                ),
            ),
        ),
    )
    assert validate_scenario_spine_definition(spine) == []
    spine_dict = scenario_spine_to_dict(spine)

    def _fake_call_gpt(_messages):
        return _gm_response('Tavern Runner says, "The east road keeps the best clue."')

    branch_rows: list[dict] = []
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)

        for branch in spine.branches:
            result = run_golden_replay(
                scenario_id=f"scenario_spine_three_branch::{branch.branch_id}",
                turns=[turn.player_prompt for turn in branch.turns],
                tmp_path=tmp_path / branch.branch_id,
                monkeypatch=monkeypatch,
                setup_fn=_seed_spine_three_branch_context,
            )
            assert result["turn_count"] == len(branch.turns)
            for i, turn in enumerate(result["turns"]):
                meta = minimal_complete_transcript_turn_meta(
                    spine_id=spine.spine_id,
                    branch_id=branch.branch_id,
                    turn_id=branch.turns[i].turn_id,
                    turn_index=i,
                    smoke=True,
                    max_turns=len(branch.turns),
                )
                assert meta["scenario_spine"]["branch_id"] == branch.branch_id
                assert_golden_turn_observation(
                    turn,
                    {
                        "require_present": ["final_text"],
                        "allow_unavailable": [
                            "fallback_family",
                            "selected_speaker_id",
                            "final_emitted_source",
                            "trace.canonical_entry",
                            "trace.social_contract_trace",
                        ],
                        "scaffold_leakage": False,
                    },
                    debug_context=format_golden_replay_debug(result),
                )
            last = result["turns"][-1]
            branch_rows.append(
                {
                    "branch_id": branch.branch_id,
                    "turn_count": result["turn_count"],
                    "route_kind": last.get("route_kind"),
                    "selected_speaker_id": last.get("selected_speaker_id"),
                    "final_emitted_source": last.get("final_emitted_source"),
                    "fallback_family": last.get("fallback_family"),
                }
            )

    assert [row["branch_id"] for row in branch_rows] == [branch.branch_id for branch in spine.branches]
    assert {row["turn_count"] for row in branch_rows} == {1}
    assert len({(row["route_kind"], row["selected_speaker_id"]) for row in branch_rows}) >= 2
    assert [b["branch_id"] for b in spine_dict["branches"]] == sorted(row["branch_id"] for row in branch_rows)
