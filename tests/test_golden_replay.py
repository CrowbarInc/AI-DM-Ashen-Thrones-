from __future__ import annotations

import json
from pathlib import Path

import pytest

from game import storage
from game.defaults import default_scene, default_world
import game.final_emission_gate as feg
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    opening_fallback_owner_bucket_from_meta,
    read_final_emission_meta_dict,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from game.upstream_response_repairs import OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
from game.scenario_spine import (
    ScenarioBranch,
    ScenarioSpine,
    ScenarioTurn,
    scenario_spine_to_dict,
    validate_scenario_spine_definition,
)
from game.scenario_spine_eval import minimal_complete_transcript_turn_meta
from tests.helpers.golden_replay import (
    _observed_turn,
    assert_golden_turn_observation,
    assert_protected_golden_turn_observation,
    classify_golden_drift,
    evaluate_golden_replay_continuity_drift,
    final_text_has_scaffold_leakage,
    format_golden_replay_debug,
    render_golden_replay_markdown_report,
    render_long_session_replay_summary_markdown,
    run_golden_replay,
    summarize_long_session_replay_observations,
)
from tests.helpers.failure_dashboard_report import (
    clear_recorded_failure_dashboard_rows,
    clear_recorded_protected_replay_failures,
    recorded_protected_replay_failure_rows,
    recorded_runtime_lineage_events,
    write_protected_replay_failure_report_if_present,
)
from tests.helpers.opening_fallback_evidence import fail_closed_opening_fem_meta, successful_opening_fem_meta
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

# Ownership note:
# Golden replay owns replay observation and projection contracts. Repeated
# route/speaker/fallback/final-emission fields are intentional diagnostic locks,
# not runtime ownership of those subsystems.

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTIER_GATE_LONG_SESSION_PATH = REPO_ROOT / "data" / "validation" / "scenario_spines" / "frontier_gate_long_session.json"


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


def _seed_frontier_gate_long_session_context() -> None:
    scene = default_scene("frontier_gate")
    scene["scene"]["id"] = "frontier_gate"
    scene["scene"]["location"] = "Cinderwatch Gate District"
    scene["scene"]["summary"] = (
        "Rain, choke traffic, a notice board, and gate watch pressure frame the missing patrol inquiry."
    )
    scene["scene"]["visible_facts"] = [
        "The notice board lists taxes, curfew rules, and a warning about a missing patrol.",
        "A gate serjeant manages the crowd and keeps one eye on the roster board.",
        "A tavern runner trades hot stew and rumors near the rain barrel.",
        "Threadbare watchers and refugees cluster along the muddy gate line.",
        "Ash Compact census delays have tightened the eastern caravan choke point.",
    ]
    scene["scene"]["interactables"] = [
        {
            "id": "notice_board",
            "label": "Notice board",
            "aliases": ["notice", "board", "curfew notice", "missing patrol warning"],
            "type": "investigate",
            "reveals_clue": "notice_patrol_route",
        }
    ]
    scene["scene"]["discoverable_clues"] = [
        {
            "id": "notice_patrol_route",
            "text": "The missing patrol was last seen taking the northwest mud track past the crates.",
        }
    ]
    storage._save_json(storage.scene_path("frontier_gate"), scene)

    world = default_world()
    world["npcs"] = [
        {
            "id": "gate_guard",
            "name": "Gate Guard",
            "location": "frontier_gate",
            "aliases": ["guard", "watch", "watch guard"],
            "topics": [
                {
                    "id": "watch_command",
                    "text": "Captain Thoran commands the gate watch tonight.",
                    "clue_id": "captain_thoran_watch",
                }
            ],
        },
        {
            "id": "gate_serjeant",
            "name": "Gate Serjeant",
            "location": "frontier_gate",
            "aliases": ["serjeant", "watch serjeant", "gate serjeant"],
            "topics": [
                {
                    "id": "route_change",
                    "text": "The patrol route changed after the Ash Compact census choke worsened.",
                    "clue_id": "patrol_route_change",
                }
            ],
        },
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "aliases": ["runner", "tavern runner"],
            "topics": [
                {
                    "id": "patrol_rumor",
                    "text": "The runner heard the patrol vanished near muddy footprints northwest of the crates.",
                    "clue_id": "muddy_footprints_northwest",
                }
            ],
        },
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    storage.save_session(session)


def _frontier_gate_branch_prompts(branch_id: str, limit: int) -> list[str]:
    raw = json.loads(FRONTIER_GATE_LONG_SESSION_PATH.read_text(encoding="utf-8"))
    branch = next(b for b in raw["branches"] if b["branch_id"] == branch_id)
    return [str(turn["player_prompt"]) for turn in branch["turns"][:limit]]


def _frontier_gate_branch_turn_ids(branch_id: str, limit: int) -> list[str]:
    raw = json.loads(FRONTIER_GATE_LONG_SESSION_PATH.read_text(encoding="utf-8"))
    branch = next(b for b in raw["branches"] if b["branch_id"] == branch_id)
    return [str(turn["turn_id"]) for turn in branch["turns"][:limit]]


def _frontier_gate_long_session_spine() -> dict:
    return json.loads(FRONTIER_GATE_LONG_SESSION_PATH.read_text(encoding="utf-8"))


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


def test_protected_golden_assertion_failure_records_canonical_report(tmp_path):
    turn = {
        "turn_index": 0,
        "final_text": 'Gate Guard says, "No names."',
        "route_kind": "dialogue",
        "selected_speaker_id": "guard",
        "final_emitted_source": "generated_candidate",
        "fallback_family": None,
        "scaffold_leakage": False,
        "unavailable": [],
        "runtime_lineage_events": [
            make_runtime_lineage_event(
                event_kind="gate_outcome",
                stage="gate",
                owner="game.final_emission_gate",
                gate_path="accept_unchanged",
            )
        ],
        "trace": {
            "canonical_entry": {"target_actor_id": "runner"},
            "social_contract_trace": {"route_selected": "dialogue"},
        },
    }
    report_path = tmp_path / "replay_failure_report.md"
    clear_recorded_protected_replay_failures()
    try:
        assert write_protected_replay_failure_report_if_present(path=report_path) is None
        with pytest.raises(AssertionError) as exc:
            assert_protected_golden_turn_observation(
                turn,
                {"equals": {"selected_speaker_id": "runner"}},
                scenario_id="synthetic_protected_bridge",
                debug_context="synthetic reporting bridge context",
            )
        assert "golden replay expectation failed: exact value mismatch" in str(exc.value)

        rows = recorded_protected_replay_failure_rows()
        assert len(rows) == 1
        assert rows[0]["scenario_id"] == "synthetic_protected_bridge"
        assert rows[0]["field_path"] == "selected_speaker_id"
        assert rows[0]["expected"] == "runner"
        assert rows[0]["actual"] == "guard"
        assert rows[0]["category"] == "speaker"
        assert rows[0]["severity"] == "critical"
        assert rows[0]["primary_owner"] == "speaker"
        assert rows[0]["investigate_first"] == "game/speaker_contract_enforcement.py"

        written = write_protected_replay_failure_report_if_present(
            path=report_path,
            command_used="python -m pytest -m golden_replay -q",
            generated_at="2026-05-26T00:00:00Z",
        )
        assert written == report_path
        report = report_path.read_text(encoding="utf-8")
        assert "# Protected Replay Failure Report" in report
        assert "synthetic_protected_bridge" in report
        assert "selected_speaker_id: exact value mismatch" in report
        assert "structural_drift" in report
        assert "game/speaker_contract_enforcement.py" in report
        assert "## Sanitizer Summary" in report
        assert "## Runtime Lineage Summary" in report
        assert "python -m pytest -m golden_replay -q" in report
    finally:
        clear_recorded_protected_replay_failures()


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


def test_golden_drift_classification_ignores_runtime_lineage_diagnostics():
    observed = {
        "scenario_id": "lineage_diagnostic_only",
        "turn_index": 0,
        "final_text": "The runner answers.",
        "route_kind": "dialogue",
        "unavailable": [],
    }
    expectation = {"equals": {"route_kind": "dialogue"}}
    baseline = classify_golden_drift(observed, expectation)
    with_lineage = classify_golden_drift(
        {
            **observed,
            "runtime_lineage_events": [
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="scene_opening",
                )
            ],
        },
        expectation,
    )
    assert with_lineage == baseline


def test_golden_drift_opt_in_dashboard_records_lineage_outside_classification_rows(monkeypatch):
    event = make_runtime_lineage_event(
        event_kind="gate_outcome",
        stage="gate",
        owner="game.final_emission_gate",
        gate_path="accept_unchanged",
    )
    clear_recorded_failure_dashboard_rows()
    monkeypatch.setenv("ASHEN_WRITE_FAILURE_DASHBOARD", "1")
    try:
        drift = classify_golden_drift(
            {
                "scenario_id": "recorded_lineage",
                "turn_index": 0,
                "final_text": "The runner answers.",
                "route_kind": "dialogue",
                "unavailable": [],
                "runtime_lineage_events": [event],
            },
            {"equals": {"route_kind": "dialogue"}},
        )
        assert drift["status"] == "pass"
        assert drift["failure_classifications"] == []
        assert recorded_runtime_lineage_events() == [event]
    finally:
        clear_recorded_failure_dashboard_rows()


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
    assert "| Scenario | Mode | Turns | Status | Drift | Classifications |" in report


def test_long_session_replay_summary_renderer_surfaces_operator_metrics():
    turns = [
        {
            "turn_index": 0,
            "route_kind": "dialogue",
            "selected_speaker_id": "runner",
            "post_gate_mutation_detected": False,
            "unavailable": [],
            "runtime_lineage_events": [],
        },
        {
            "turn_index": 1,
            "route_kind": "dialogue",
            "selected_speaker_id": "runner",
            "post_gate_mutation_detected": True,
            "unavailable": ["fallback_family"],
            "runtime_lineage_events": [
                {
                    "event_type": "runtime_lineage",
                    "event_kind": "fallback_selected",
                    "stage": "gate",
                    "owner": "game.final_emission_gate",
                    "source": "neutral_reply_speaker_grounding_bridge",
                    "fallback_kind": "sealed_or_global_replacement",
                    "recurrence_key": "fallback_selected:gate:game.final_emission_gate:sealed_or_global_replacement",
                }
            ],
        },
    ]
    summary = {
        "turn_count": 2,
        "route_frequency": {"dialogue": 2},
        "route_change_count": 0,
        "speaker_frequency": {"runner": 2},
        "speaker_change_count": 0,
        "speaker_missing_count": 0,
        "mutation_turn_count": 1,
        "unavailable_counts": {"fallback_family": 1},
        "lineage_summary": {
            "by_event_kind": {"fallback_selected": 1},
            "recurring_events": [
                {
                    "recurrence_key": "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
                    "count": 2,
                }
            ],
        },
        "fallback_escalation_summary": {
            "fallback_total_count": 1,
            "fallback_family_counts": {},
            "fallback_owner_counts": {},
            "fallback_lineage_kind_counts": {"sealed_or_global_replacement": 1},
            "max_fallback_streak": 1,
            "late_window_fallback_count": 0,
            "escalation_warnings": [],
        },
        "continuity_warning_count": 0,
        "continuity_violation_count": 0,
        "continuity_drift": {
            "session_health": {"classification": "clean", "degradation_detected": False},
            "degradation_over_time": {"reason_codes": [], "late_window": {"signals": []}},
        },
    }

    report = render_long_session_replay_summary_markdown(
        scenario_id="synthetic_long_session",
        turns=turns,
        summary=summary,
        title="Synthetic Long Session",
    )

    assert "- Route changes: `0`" in report
    assert "- Speaker changes / missing: `0` / `0`" in report
    assert "- Continuity classification: `clean`" in report
    assert "- Fallback total count: `1`" in report
    assert "- Fallback lineage kinds: `{'sealed_or_global_replacement': 1}`" in report
    assert "- Mutation turn count: `1`" in report
    assert "- Unavailable counts: `{'fallback_family': 1}`" in report
    assert "- Lineage recurrence: `[" in report
    assert "- Fallback frequency:" not in report
    assert "- Mutation turns:" not in report


# Opening fallback projection fields are repeated here as replay contract locks;
# the owner-bucket mapper itself is owned by tests/test_opening_fallback_owner_bucket.py.
def test_golden_observed_turn_projects_canonical_upstream_prepared_opening_owner_bucket():
    observed = _observed_turn(
        scenario_id="synthetic_opening_owner",
        snap={"turn_index": 0, "gm_text": "The road opens."},
        payload={
            "gm_output": {
                "_final_emission_meta": successful_opening_fem_meta(
                    response_type_repair_kind="opening_deterministic_fallback",
                    fallback_temporal_frame="first_impression",
                )
            }
        },
    )

    assert observed["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED


def test_golden_observed_turn_projects_runtime_lineage_and_prefers_existing_events():
    existing = make_runtime_lineage_event(
        event_kind="speaker_repair",
        stage="gate",
        owner="game.speaker_contract_enforcement",
        source="provided_projection",
        repair_kind="local_rebind",
    )
    observed = _observed_turn(
        scenario_id="existing_lineage_projection",
        snap={"turn_index": 0, "gm_text": "The road opens."},
        payload={
            "gm_output": {
                "metadata": {"observability_bundle": {"fem_runtime_lineage_events": [existing]}},
                "_final_emission_meta": {
                    "final_emitted_source": "opening_deterministic_fallback",
                    "opening_recovered_via_fallback": True,
                    "fallback_family_used": "scene_opening",
                },
            }
        },
    )
    assert observed["runtime_lineage_events"] == [existing]

    from_fem = _observed_turn(
        scenario_id="fem_lineage_projection",
        snap={"turn_index": 0, "gm_text": "The road opens."},
        payload={
            "gm_output": {
                "_final_emission_meta": successful_opening_fem_meta()
            }
        },
    )
    opening_selected = next(
        event for event in from_fem["runtime_lineage_events"] if event["event_kind"] == "fallback_selected"
    )
    assert opening_selected["fallback_kind"] == "scene_opening"
    assert opening_selected["owner"] == "game.final_emission_gate"
    assert opening_selected["fallback_authorship_source"] == "upstream_prepared_opening_fallback"
    assert opening_selected["fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    debug = format_golden_replay_debug(
        {"scenario_id": from_fem["scenario_id"], "turn_count": 1, "turns": [from_fem]}
    )
    assert "'fallback_authorship_source': 'upstream_prepared_opening_fallback'" in debug
    assert "'fallback_owner_bucket': 'upstream-prepared'" in debug

    missing = _observed_turn(
        scenario_id="missing_lineage_projection",
        snap={"turn_index": 0, "gm_text": "The road remains quiet."},
        payload={"gm_output": {"player_facing_text": "The road remains quiet."}},
    )
    assert missing["runtime_lineage_events"] == []


def test_golden_observed_turn_projects_fail_closed_sealed_gate_opening_owner_bucket():
    observed = _observed_turn(
        scenario_id="synthetic_opening_owner_fail_closed",
        snap={"turn_index": 0, "gm_text": "[opening_fallback_failed_closed:no_curated_facts]"},
        payload={
            "gm_output": {
                "_final_emission_meta": fail_closed_opening_fem_meta(
                    opening_recovered_via_fallback=True,
                    fallback_family_used="scene_opening",
                )
            }
        },
    )

    assert observed["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_SEALED_GATE
    failed_closed_selected = next(
        event for event in observed["runtime_lineage_events"] if event["event_kind"] == "fallback_selected"
    )
    assert failed_closed_selected["fallback_kind"] == "opening_failed_closed"
    assert failed_closed_selected["fallback_authorship_source"] is None
    assert failed_closed_selected["fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_SEALED_GATE
    debug = format_golden_replay_debug(
        {"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]}
    )
    assert "'fallback_kind': 'opening_failed_closed'" in debug
    assert "'fallback_owner_bucket': 'sealed-gate'" in debug


# Sealed fallback projection fields are replay contract locks. Helper shaping is
# owned by final_emission_sealed_fallback; gate branch selection/output remains
# owned by final_emission_gate.
def test_golden_observed_turn_projects_sealed_fallback_owner_bucket():
    observed = _observed_turn(
        scenario_id="synthetic_sealed_owner",
        snap={"turn_index": 0, "gm_text": "A sealed fallback line."},
        payload={
            "gm_output": {
                "_final_emission_meta": {
                    "final_route": "replaced",
                    "final_emitted_source": "global_scene_fallback",
                    "sealed_fallback_owner_bucket": SEALED_FALLBACK_OWNER_SEALED_GATE,
                    "realization_fallback_family": "gate_terminal_repair",
                }
            }
        },
    )

    assert observed["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_SEALED_GATE


def test_golden_observed_turn_projects_strict_social_sealed_fallback_owner_bucket():
    observed = _observed_turn(
        scenario_id="synthetic_strict_social_sealed_owner",
        snap={"turn_index": 0, "gm_text": "A strict-social sealed fallback line."},
        payload={
            "gm_output": {
                "_final_emission_meta": {
                    "final_route": "replaced",
                    "final_emitted_source": "minimal_social_emergency_fallback",
                    "sealed_fallback_owner_bucket": SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
                    "realization_fallback_family": "strict_social_deterministic_fallback",
                }
            }
        },
    )

    assert observed["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED


def test_golden_observed_turn_projects_visibility_fallback_evidence():
    observed = _observed_turn(
        scenario_id="synthetic_visibility_owner",
        snap={"turn_index": 0, "gm_text": "A visibility fallback line."},
        payload={
            "gm_output": {
                "_final_emission_meta": {
                    "final_route": "replaced",
                    "final_emitted_source": "global_scene_fallback",
                    "visibility_fallback_owner_bucket": "sealed-gate",
                    "visibility_replacement_applied": True,
                    "visibility_fallback_pool": "global_scene_narrative",
                    "visibility_fallback_kind": "narrative_safe_fallback",
                    "sealed_fallback_owner_bucket": SEALED_FALLBACK_OWNER_SEALED_GATE,
                }
            }
        },
    )

    assert observed["visibility_fallback_owner_bucket"] == "sealed-gate"
    assert observed["visibility_replacement_applied"] is True
    assert observed["visibility_fallback_pool"] == "global_scene_narrative"
    assert observed["visibility_fallback_kind"] == "narrative_safe_fallback"


@pytest.mark.parametrize(
    ("required", "repair_kind", "source"),
    [
        (
            "answer",
            "answer_upstream_prepared_repair",
            "upstream_prepared_emission.prepared_answer_fallback_text",
        ),
        (
            "action_outcome",
            "action_outcome_upstream_prepared_repair",
            "upstream_prepared_emission.prepared_action_fallback_text",
        ),
    ],
)
def test_golden_observed_turn_projects_valid_upstream_prepared_emission_telemetry(required, repair_kind, source):
    observed = _observed_turn(
        scenario_id=f"{required}_prepared_projection",
        snap={"turn_index": 0, "player_text": "Do the thing.", "gm_text": "Projected prepared text."},
        payload={
            "resolution": {"kind": "investigate"},
            "gm_output": {
                "_final_emission_meta": {
                    "final_emitted_source": repair_kind,
                    "response_type_required": required,
                    "response_type_candidate_ok": True,
                    "response_type_repair_used": True,
                    "response_type_repair_kind": repair_kind,
                    "upstream_prepared_emission_used": True,
                    "upstream_prepared_emission_valid": True,
                    "upstream_prepared_emission_source": source,
                    "upstream_prepared_emission_reject_reason": None,
                    "realization_fallback_family": "upstream_prepared_emission",
                }
            },
        },
    )

    assert observed["upstream_prepared_emission_used"] is True
    assert observed["upstream_prepared_emission_valid"] is True
    assert observed["upstream_prepared_emission_source"] == source
    assert observed["upstream_prepared_emission_reject_reason"] is None
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert f"upstream_prepared_emission_source: {source!r}" in debug


def test_golden_observed_turn_projects_rejected_upstream_prepared_emission_telemetry():
    observed = _observed_turn(
        scenario_id="rejected_prepared_projection",
        snap={"turn_index": 0, "player_text": "Pry the chest.", "gm_text": "You pry the chest, but nothing gives yet."},
        payload={
            "resolution": {"kind": "investigate"},
            "gm_output": {
                "_final_emission_meta": {
                    "final_emitted_source": "generated_candidate",
                    "response_type_required": "action_outcome",
                    "response_type_candidate_ok": False,
                    "response_type_repair_used": False,
                    "response_type_repair_kind": "action_outcome_upstream_prepared_repair",
                    "upstream_prepared_emission_used": False,
                    "upstream_prepared_emission_valid": False,
                    "upstream_prepared_emission_source": "upstream_prepared_emission.prepared_action_fallback_text",
                    "upstream_prepared_emission_reject_reason": "action_outcome_replaced_by_dialogue",
                    "realization_fallback_family": "upstream_prepared_emission",
                }
            },
        },
    )

    assert observed["upstream_prepared_emission_used"] is False
    assert observed["upstream_prepared_emission_valid"] is False
    assert observed["upstream_prepared_emission_source"] == "upstream_prepared_emission.prepared_action_fallback_text"
    assert observed["upstream_prepared_emission_reject_reason"] == "action_outcome_replaced_by_dialogue"
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "upstream_prepared_emission_reject_reason: 'action_outcome_replaced_by_dialogue'" in debug


@pytest.mark.parametrize(
    ("required", "repair_kind", "source"),
    [
        ("answer", None, "absent"),
        ("action_outcome", None, "absent"),
    ],
)
def test_golden_observed_turn_projects_absent_upstream_prepared_emission_telemetry(required, repair_kind, source):
    observed = _observed_turn(
        scenario_id=f"{required}_prepared_absent_projection",
        snap={"turn_index": 0, "player_text": "Can I do it?", "gm_text": "Only mist between the torches."},
        payload={
            "resolution": {"kind": "investigate"},
            "gm_output": {
                "_final_emission_meta": {
                    "final_emitted_source": "generated_candidate",
                    "response_type_required": required,
                    "response_type_candidate_ok": False,
                    "response_type_repair_used": False,
                    "response_type_repair_kind": repair_kind,
                    "response_type_upstream_prepared_absent": True,
                    "upstream_prepared_emission_used": False,
                    "upstream_prepared_emission_valid": False,
                    "upstream_prepared_emission_source": source,
                    "upstream_prepared_emission_reject_reason": None,
                }
            },
        },
    )

    assert observed["upstream_prepared_emission_used"] is False
    assert observed["upstream_prepared_emission_valid"] is False
    assert observed["upstream_prepared_emission_source"] == "absent"
    assert observed["upstream_prepared_emission_reject_reason"] is None
    assert observed["raw_signal_presence"]["upstream_prepared_emission_used"] is True
    assert observed["raw_signal_presence"]["upstream_prepared_emission_valid"] is True
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "upstream_prepared_emission_used: False" in debug
    assert "upstream_prepared_emission_source: 'absent'" in debug


def test_golden_drift_classification_preserves_malformed_prepared_emission_reject_reason():
    observed = _observed_turn(
        scenario_id="malformed_prepared_projection",
        snap={"turn_index": 0, "player_text": "Pry the lock.", "gm_text": "The lock remains stubborn."},
        payload={
            "resolution": {"kind": "investigate"},
            "gm_output": {
                "_final_emission_meta": {
                    "final_emitted_source": "generated_candidate",
                    "response_type_required": "action_outcome",
                    "response_type_candidate_ok": False,
                    "response_type_repair_used": False,
                    "response_type_repair_kind": "action_outcome_upstream_prepared_repair",
                    "upstream_prepared_emission_used": True,
                    "upstream_prepared_emission_valid": False,
                    "upstream_prepared_emission_source": "upstream_prepared_emission.prepared_action_fallback_text",
                    "upstream_prepared_emission_reject_reason": "action_outcome_missing_result",
                    "realization_fallback_family": "upstream_prepared_emission",
                }
            },
        },
    )

    drift = classify_golden_drift(
        observed,
        {
            "equals": {
                "upstream_prepared_emission_valid": True,
            }
        },
    )

    assert observed["upstream_prepared_emission_used"] is True
    assert observed["upstream_prepared_emission_valid"] is False
    assert observed["upstream_prepared_emission_reject_reason"] == "action_outcome_missing_result"
    row = drift["failure_classifications"][0]
    assert row["primary_owner"] == "upstream_prepared_emission"
    assert row["upstream_prepared_emission_reject_reason"] == "action_outcome_missing_result"
    debug = format_golden_replay_debug(
        {"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed], "drift": drift}
    )
    assert "upstream_prepared_emission_reject_reason: 'action_outcome_missing_result'" in debug
    assert "owner='upstream_prepared_emission'" in debug


def test_golden_observed_turn_projects_sanitizer_empty_fallback_as_sanitizer_owned():
    observed = _observed_turn(
        scenario_id="sanitizer_empty_projection",
        snap={"turn_index": 0, "player_text": "Wait.", "gm_text": "For a breath, the scene stays still."},
        payload={
            "resolution": {"kind": "observe"},
            "gm_output": {
                "metadata": {
                    "sanitizer_trace": {
                        "sanitizer_boundary_mode": "strip_only",
                        "sanitizer_empty_fallback_used": True,
                        "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                        "sanitizer_empty_fallback_owner": "output_sanitizer",
                    }
                },
                "_final_emission_meta": {
                    "final_emitted_source": "generated_candidate",
                    "final_emission_mutation_lineage": [
                        "pre_gate_sanitizer",
                        "sanitizer_empty_fallback",
                        "finalize_packaging",
                    ],
                    "response_type_repair_used": False,
                    "upstream_prepared_emission_used": False,
                    "upstream_prepared_emission_valid": False,
                    "upstream_prepared_emission_source": None,
                    "upstream_prepared_emission_reject_reason": None,
                },
            },
        },
    )

    assert observed["sanitizer_empty_fallback_used"] is True
    assert observed["sanitizer_empty_fallback_source"] == "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text"
    assert observed["sanitizer_empty_fallback_owner"] == "output_sanitizer"
    assert observed["upstream_prepared_emission_used"] is False
    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_empty_fallback_used"] is True
    assert "sanitizer_empty_fallback" in observed["final_emission_mutation_lineage"]
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "sanitizer_empty_fallback_owner: 'output_sanitizer'" in debug
    assert "sanitizer_lineage_empty_fallback_used: True" in debug
    assert "final_emission_mutation_lineage" in debug


def test_golden_observed_turn_projects_strict_social_sanitizer_fallback_owner_split():
    observed = _observed_turn(
        scenario_id="strict_social_sanitizer_split",
        snap={"turn_index": 0, "player_text": "Ask the runner.", "gm_text": 'The runner says, "No names."'},
        payload={
            "resolution": {"kind": "question"},
            "gm_output": {
                "metadata": {
                    "sanitizer_trace": {
                        "sanitizer_lineage_mode": "strip_only",
                        "sanitizer_strict_social_fallback_used": True,
                        "sanitizer_strict_social_selection_owner": "output_sanitizer",
                        "sanitizer_strict_social_prose_owner": "strict_social_emission",
                        "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
                    }
                },
                "_final_emission_meta": {
                    "final_emitted_source": "generated_candidate",
                    "strict_social_active": True,
                    "upstream_prepared_emission_used": False,
                    "upstream_prepared_emission_valid": False,
                    "upstream_prepared_emission_source": None,
                    "upstream_prepared_emission_reject_reason": None,
                },
            },
        },
    )

    assert observed["sanitizer_strict_social_fallback_used"] is True
    assert observed["sanitizer_strict_social_selection_owner"] == "output_sanitizer"
    assert observed["sanitizer_strict_social_prose_owner"] == "strict_social_emission"
    assert observed["sanitizer_strict_social_source"] == "social_fallback_line_for_sanitizer.empty_output"
    assert observed["sanitizer_empty_fallback_used"] is None
    assert observed["upstream_prepared_emission_used"] is False
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "sanitizer_strict_social_selection_owner: 'output_sanitizer'" in debug
    assert "sanitizer_strict_social_prose_owner: 'strict_social_emission'" in debug


def test_golden_observed_turn_projects_clean_sanitizer_lineage():
    observed = _observed_turn(
        scenario_id="sanitizer_clean_lineage",
        snap={"turn_index": 0, "player_text": "Wait.", "gm_text": "Rain needles across the checkpoint."},
        payload={
            "resolution": {"kind": "observe"},
            "gm_output": {
                "metadata": {
                    "sanitizer_trace": {
                        "sanitizer_lineage_mode": "strip_only",
                        "sanitizer_lineage_changed_count": 0,
                        "sanitizer_lineage_dropped_count": 0,
                        "sanitizer_lineage_empty_fallback_used": False,
                        "sanitizer_lineage_legacy_rewrite_active": False,
                    }
                },
                "_final_emission_meta": {"final_emitted_source": "generated_candidate"},
            },
        },
    )

    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_changed_count"] == 0
    assert observed["sanitizer_lineage_dropped_count"] == 0
    assert observed["sanitizer_lineage_empty_fallback_used"] is False
    assert observed["sanitizer_lineage_legacy_rewrite_active"] is False


def test_golden_observed_turn_projects_sanitizer_lineage_from_debug_events():
    observed = _observed_turn(
        scenario_id="sanitizer_debug_lineage",
        snap={"turn_index": 0, "player_text": "Wait.", "gm_text": ""},
        payload={
            "resolution": {"kind": "observe"},
            "gm_output": {
                "metadata": {
                    "sanitizer_trace": {"sanitizer_boundary_mode": "strip_only"},
                    "sanitizer_debug": [
                        {"event": "strip_only_dropped_rewrite_candidate", "sentence": "Validator scaffold."},
                        {"event": "strip_only_dropped_non_diegetic", "sentence": "Planner scaffold."},
                    ],
                },
                "_final_emission_meta": {"final_emitted_source": "generated_candidate"},
            },
        },
    )

    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_changed_count"] == 2
    assert observed["sanitizer_lineage_dropped_count"] == 2


def test_golden_observed_turn_projects_legacy_sanitizer_lineage():
    observed = _observed_turn(
        scenario_id="sanitizer_legacy_lineage",
        snap={"turn_index": 0, "player_text": "Wait.", "gm_text": "The answer has not formed yet."},
        payload={
            "resolution": {"kind": "observe"},
            "gm_output": {
                "metadata": {
                    "sanitizer_trace": {
                        "sanitizer_lineage_mode": "legacy_sentence_rewrite",
                        "sanitizer_lineage_changed_count": 1,
                        "sanitizer_lineage_dropped_count": 0,
                        "sanitizer_lineage_empty_fallback_used": False,
                        "sanitizer_lineage_legacy_rewrite_active": True,
                    }
                },
                "_final_emission_meta": {"final_emitted_source": "generated_candidate"},
            },
        },
    )

    assert observed["sanitizer_lineage_mode"] == "legacy_sentence_rewrite"
    assert observed["sanitizer_lineage_legacy_rewrite_active"] is True


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
    assert_protected_golden_turn_observation(
        turn,
        directed_npc_question_expectation,
        scenario_id="directed_npc_question",
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
    assert_protected_golden_turn_observation(
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
        scenario_id="vocative_override_after_prior_continuity",
        debug_context=debug_context,
    )
    if "route_kind" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
            turn,
            {"allow_unavailable": ["fallback_family"], "one_of": {"route_kind": ["social", "question", "social_engine", "dialogue"]}},
            scenario_id="vocative_override_after_prior_continuity",
            debug_context=debug_context,
        )
    canonical_entry = (turn.get("trace") or {}).get("canonical_entry") or {}
    if canonical_entry:
        assert_protected_golden_turn_observation(
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
            scenario_id="vocative_override_after_prior_continuity",
            debug_context=debug_context,
        )
    social_contract_trace = (turn.get("trace") or {}).get("social_contract_trace") or {}
    if social_contract_trace.get("route_selected") is not None:
        assert_protected_golden_turn_observation(
            turn,
            {
                "allow_unavailable": ["fallback_family"],
                "one_of": {"trace.social_contract_trace.route_selected": ["social", "dialogue"]},
            },
            scenario_id="vocative_override_after_prior_continuity",
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
    assert_protected_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text", "selected_speaker_id"],
            "allow_unavailable": ["fallback_family", "final_emitted_source"],
            "equals": {"selected_speaker_id": "runner"},
            "text_must_not_include": ["Merchant", "planner", "router", "validator", "adjudication", "scaffold"],
            "scaffold_leakage": False,
        },
        scenario_id="wrong_speaker_strict_social_emission",
        debug_context=debug_context,
    )
    if "final_emitted_source" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
            turn,
            {"allow_unavailable": ["fallback_family"], "require_present": ["final_emitted_source"]},
            scenario_id="wrong_speaker_strict_social_emission",
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

    assert_protected_golden_turn_observation(
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
        scenario_id="declared_alias_dialogue_plan",
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
    assert_protected_golden_turn_observation(
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
        scenario_id="thin_answer_action_outcome_final_emission",
        debug_context=debug_context,
    )
    assert "patrol" in low or "east ridge" in low or "notice" in low, debug_context
    assert turn.get("sanitizer_lineage_legacy_rewrite_active") is not True


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
    assert turn.get("sanitizer_lineage_legacy_rewrite_active") is not True
    assert_protected_golden_turn_observation(
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
        scenario_id="sanitizer_scaffold_leakage",
        debug_context=format_golden_replay_debug(result),
    )
    if "final_emitted_source" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
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
            scenario_id="sanitizer_scaffold_leakage",
            debug_context=format_golden_replay_debug(result),
        )


def test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership():
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
        "opening_fallback_owner_bucket": opening_fallback_owner_bucket_from_meta(meta),
        "fallback_family": meta.get("fallback_family_used") or meta.get("realization_fallback_family"),
        "fallback_temporal_frame": meta.get("fallback_temporal_frame"),
        "scaffold_leakage": final_text_has_scaffold_leakage(final_text),
        "unavailable": [],
    }

    assert_protected_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text", "final_emitted_source", "fallback_family", "opening_fallback_owner_bucket"],
            "equals": {
                "final_emitted_source": "opening_deterministic_fallback",
                "response_type_required": "scene_opening",
                "response_type_repair_used": True,
                "response_type_repair_kind": "opening_deterministic_fallback",
                "opening_recovered_via_fallback": True,
                "opening_fallback_authorship_source": "upstream_prepared_opening_fallback",
                "opening_fallback_owner_bucket": OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
                "fallback_family": "scene_opening",
                "fallback_temporal_frame": "first_impression",
            },
            "not_equals": {
                "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
            },
            "text_must_not_include": ["planner", "router", "validator", "adjudication", "scaffold"],
            "scaffold_leakage": False,
        },
        scenario_id="opening_fallback_path",
        debug_context=f"meta={meta!r}; final_text={final_text!r}",
    )
    assert turn["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    assert turn["opening_fallback_authorship_source"] != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL


def test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership():
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

    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert opening_fallback_owner_bucket_from_meta(meta) == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED


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
    assert_protected_golden_turn_observation(
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
        scenario_id="lead_followup_with_dialogue_lock",
        debug_context=debug_context,
    )
    canonical_entry = (turn.get("trace") or {}).get("canonical_entry") or {}
    if canonical_entry:
        assert_protected_golden_turn_observation(
            turn,
            {
                "allow_unavailable": ["fallback_family"],
                "equals": {"trace.canonical_entry.target_actor_id": "tavern_runner"},
            },
            scenario_id="lead_followup_with_dialogue_lock",
            debug_context=debug_context,
        )


def test_golden_replay_frontier_gate_social_inquiry_20_turn_structural_stability(tmp_path, monkeypatch):
    turns = _frontier_gate_branch_prompts("branch_social_inquiry", 20)
    turn_ids = _frontier_gate_branch_turn_ids("branch_social_inquiry", 20)
    spine = _frontier_gate_long_session_spine()
    assert len(turns) == 20

    gpt_call_count = 0

    def _fake_call_gpt(_messages):
        nonlocal gpt_call_count
        gpt_call_count += 1
        return _gm_response(
            (
                "The gate inquiry stays anchored: the notice board, Captain Thoran, the Ash Compact census "
                "delay, muddy footprints northwest of the crates, and the missing patrol route remain in view. "
                f"The answer advances the same thread at deterministic call {gpt_call_count}."
            )
        )

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _fake_call_gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)

        result = run_golden_replay(
            scenario_id="frontier_gate_social_inquiry_20_turn",
            turns=turns,
            tmp_path=tmp_path,
            monkeypatch=monkeypatch,
            setup_fn=_seed_frontier_gate_long_session_context,
            starting_scene_id="frontier_gate",
        )

    observed_turns = result["turns"]
    summary = summarize_long_session_replay_observations(observed_turns)
    continuity_bridge = evaluate_golden_replay_continuity_drift(
        spine=spine,
        branch_id="branch_social_inquiry",
        turns=observed_turns,
        turn_ids=turn_ids,
    )
    continuity_eval = continuity_bridge["evaluation"]
    summary["continuity_drift"] = continuity_eval
    debug_context = "\n\n".join(
        [
            format_golden_replay_debug(result),
            render_long_session_replay_summary_markdown(
                scenario_id="frontier_gate_social_inquiry_20_turn",
                turns=observed_turns,
                summary=summary,
                title="Golden Replay 20-Turn Structural Stability",
            ),
        ]
    )

    assert result["turn_count"] == 20, debug_context
    assert summary["turn_count"] == 20, debug_context
    assert all(not turn.get("scaffold_leakage") for turn in observed_turns), debug_context
    assert summary["speaker_change_count"] <= 8, debug_context
    assert summary["speaker_missing_count"] <= 10, debug_context
    assert summary["fallback_turn_count"] <= 3, debug_context
    assert summary["fallback_owner_change_count"] <= 1, debug_context
    assert summary["route_change_count"] <= 8, debug_context

    route_frequency = summary["route_frequency"]
    resolved_routes = sum(route_frequency.values())
    assert resolved_routes >= 12, debug_context

    session_health = continuity_eval["session_health"]
    degradation = continuity_eval["degradation_over_time"]
    assert session_health["long_session_band"] == "standard", debug_context
    assert session_health["classification"] in {"clean", "warning"}, debug_context
    assert session_health["overall_passed"] is True, debug_context
    assert degradation["progressive_degradation_detected"] is False, debug_context
    assert "late_session_reset_or_amnesia" not in degradation["reason_codes"], debug_context
    assert "rising_generic_filler_strong" not in degradation["reason_codes"], debug_context
    assert "rising_generic_filler_progressive" not in degradation["reason_codes"], debug_context
    assert "debug_leak_late_window" not in degradation["reason_codes"], debug_context
    assert "referent_loss_late" not in degradation["reason_codes"], debug_context
    assert "continuity_anchor_late_loss" not in degradation["reason_codes"], debug_context
    assert continuity_eval["axes"]["narrative_grounding"]["passed"] is True, debug_context
    assert continuity_eval["axes"]["branch_coherence"]["passed"] is True, debug_context

    lineage_summary = summary["lineage_summary"]
    fallback_selected = lineage_summary.get("fallback_frequency") or {}
    assert sum(int(v) for v in fallback_selected.values()) <= 1, debug_context
    mutation_frequency = lineage_summary.get("mutation_kind_frequency") or {}
    assert int(mutation_frequency.get("fallback_mutation") or 0) <= 1, debug_context

    fallback_escalation = summary["fallback_escalation_summary"]
    assert fallback_escalation["fallback_total_count"] <= 1, debug_context
    assert fallback_escalation["max_fallback_streak"] <= 1, debug_context
    assert fallback_escalation["late_window_fallback_count"] == 0, debug_context
    assert fallback_escalation["fallback_owner_change_count"] == 0, debug_context
    assert fallback_escalation["fallback_lineage_owner_change_count"] == 0, debug_context
    assert fallback_escalation["fallback_behavior_repair_count"] == 0, debug_context
    assert fallback_escalation["response_type_repair_count"] <= 1, debug_context
    assert fallback_escalation["sanitizer_fallback_count"] == 0, debug_context
    assert fallback_escalation["unavailable_with_fallback_count"] <= 1, debug_context
    assert fallback_escalation["fallback_selected_without_family_count"] <= 1, debug_context
    assert fallback_escalation["escalation_warnings"] == [], debug_context
    assert fallback_escalation["model_routing_escalation_observable"] is False, debug_context


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
