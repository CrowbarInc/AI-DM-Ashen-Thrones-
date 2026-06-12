from __future__ import annotations

from tests.helpers.emission_smoke_assertions import apply_final_emission_gate_consumer
import pytest

from game import storage
from game.api import chat
from tests.helpers.golden_replay_projection import read_fem_meta_from_gate_output
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
    OPENING_FALLBACK_FAMILY,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
)
from game.scenario_spine import (
    ScenarioBranch,
    ScenarioSpine,
    ScenarioTurn,
    scenario_spine_to_dict,
    validate_scenario_spine_definition,
)
from game.scenario_spine_eval import minimal_complete_transcript_turn_meta
from game.models import ChatRequest
from tests.helpers.golden_replay import (
    FRONTIER_GATE_DIRECT_INTRUSION_LINEAGE_PROFILE,
    FRONTIER_GATE_RESUME_FALLBACK_ESCALATION_PROFILE,
    FRONTIER_GATE_RESUME_LINEAGE_PROFILE,
    FRONTIER_GATE_RESUME_STABILITY_PROFILE,
    FRONTIER_GATE_SOCIAL_INQUIRY_FALLBACK_ESCALATION_PROFILE,
    FRONTIER_GATE_SOCIAL_INQUIRY_LINEAGE_PROFILE,
    FRONTIER_GATE_SOCIAL_INQUIRY_STABILITY_PROFILE,
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    _observed_turn,
    assert_golden_replay_profile_bundle,
    assert_golden_turn_observation,
    assert_protected_golden_turn_observation,
    evaluate_golden_replay_continuity_drift,
    format_golden_replay_debug,
    frontier_gate_branch_replay_fixture,
    protected_social_directed_question_expectation,
    protected_social_structural_base,
    protected_social_supplemental_structural_expectation,
    protected_social_trace_target_expectation,
    protected_social_vocative_canonical_entry_expectation,
    protected_structural_expectation,
    render_long_session_replay_summary_markdown,
    run_golden_replay,
    summarize_long_session_replay_observations,
)
from tests.helpers.transcript_runner import (
    new_clean_campaign,
    patch_transcript_storage,
    snapshot_from_chat_payload,
    write_default_bootstrap_scenes,
)
from tests.helpers.failure_dashboard_report import (
    clear_recorded_protected_replay_failures,
    recorded_protected_replay_failure_rows,
    write_protected_replay_failure_report_if_present,
)
from tests.helpers.opening_fallback_evidence import (
    successful_opening_observed_fields,
)
from tests.helpers.dialogue_social_plan import (
    attach_dialogue_social_plan_to_resolution,
    make_valid_dialogue_social_plan,
)
from tests.helpers.block_stu_equivalence_fixtures import locked_runner_contract, stub_strict_social_details
from tests.helpers.gate_equivalence_monkeypatch import (
    patch_build_final_strict_social_response,
    patch_get_speaker_selection_contract,
)
from tests.helpers.opening_fallback_evidence import opening_gm_output
from tests.helpers.strict_social_harness import runner_strict_bundle
from tests.helpers.replay_observed_row_fixtures import protected_speaker_failure_turn
from tests.helpers.golden_replay_fixtures import (
    gm_response,
    golden_replay_chat_stubs,
    observed_turn_from_gate_output,
    seed_frontier_gate_world,
    seed_investigator_runner_world,
    seed_runner_continuity_world,
    seed_runner_guard_world,
    seed_scene_object_investigation_world,
    seed_spine_three_branch_world,
    seed_tavern_patrol_lead_world,
)

pytestmark = [pytest.mark.integration, pytest.mark.golden_replay]

# Ownership note:
# Golden replay owns protected replay orchestration and live replay bridge checks.
# Synthetic projection contracts live in ``tests.test_golden_replay_projection``.
# Repeated route/speaker/fallback/final-emission fields are intentional diagnostic
# locks, not runtime ownership of those subsystems.


def test_protected_golden_assertion_failure_records_canonical_report(tmp_path):
    turn = protected_speaker_failure_turn()
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
        assert rows[0]["source_path"] == "data/validation/scenario_spines/synthetic_fixture.json"
        assert rows[0]["branch_id"] == "synthetic_branch"
        assert rows[0]["turn_id"] == "synthetic_turn_01"
        assert rows[0]["field_path"] == "selected_speaker_id"
        assert rows[0]["expected"] == "runner"
        assert rows[0]["actual"] == "guard"
        assert rows[0]["category"] == "speaker"
        assert rows[0]["severity"] == "critical"
        assert rows[0]["primary_owner"] == "speaker"
        assert rows[0]["investigate_first"] == "game/speaker_contract_enforcement.py"
    finally:
        clear_recorded_protected_replay_failures()


def test_golden_replay_directed_npc_question_structural_invariants(tmp_path, monkeypatch):
    captured_prompts: list[list[dict]] = []

    def _fake_call_gpt(messages):
        captured_prompts.append(messages)
        return gm_response('Tavern Runner grimaces. "I heard east-road talk, but no names."')

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="directed_npc_question",
        turns=["Runner, who attacked the patrol?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_investigator_runner_world,
    )

    assert captured_prompts
    assert result["turn_count"] == 1
    turn = result["turns"][0]
    assert_protected_golden_turn_observation(
        turn,
        protected_social_directed_question_expectation("runner"),
        scenario_id="directed_npc_question",
        debug_context=format_golden_replay_debug(result),
    )


def test_golden_replay_vocative_override_after_prior_continuity_structural_invariants(tmp_path, monkeypatch):
    responses = iter(
        [
            gm_response('Tavern Runner says, "I saw the patrol turn toward the east lanes."'),
            gm_response('Gate Guard says, "I saw fresh mud by the north arch."'),
        ]
    )

    def _fake_call_gpt(_messages):
        return next(responses)

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="vocative_override_after_prior_continuity",
        turns=[
            "Runner, where did the patrol go?",
            "Guard, what did you see?",
        ],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_runner_guard_world,
    )

    assert result["turn_count"] == 2
    turn = result["turns"][1]
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
            selected_speaker_id="guard",
            require_route_kind=False,
            require_final_emitted_source=False,
            allow_unavailable=(
                "fallback_family",
                "final_emitted_source",
                "route_kind",
                "trace.canonical_entry",
                "trace.turn_trace",
                "trace.social_contract_trace",
            ),
            include_route_kind=False,
        ),
        scenario_id="vocative_override_after_prior_continuity",
        debug_context=debug_context,
    )
    if "route_kind" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
            turn,
            protected_social_supplemental_structural_expectation(),
            scenario_id="vocative_override_after_prior_continuity",
            debug_context=debug_context,
        )
    canonical_entry = (turn.get("trace") or {}).get("canonical_entry") or {}
    if canonical_entry:
        assert_protected_golden_turn_observation(
            turn,
            protected_social_vocative_canonical_entry_expectation("guard"),
            scenario_id="vocative_override_after_prior_continuity",
            debug_context=debug_context,
        )
    social_contract_trace = (turn.get("trace") or {}).get("social_contract_trace") or {}
    if social_contract_trace.get("route_selected") is not None:
        assert_protected_golden_turn_observation(
            turn,
            protected_social_supplemental_structural_expectation(include_trace_route=True),
            scenario_id="vocative_override_after_prior_continuity",
            debug_context=debug_context,
        )


def test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response('Merchant says, "I know nothing about that."'),
    )

    result = run_golden_replay(
        scenario_id="wrong_speaker_strict_social_emission",
        turns=["Who attacked the patrol?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_runner_continuity_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
            selected_speaker_id="runner",
            allow_unavailable=("fallback_family", "final_emitted_source"),
            require_route_kind=False,
            require_final_emitted_source=False,
            include_route_kind=False,
            extra_no_scaffold_terms=("Merchant",),
        ),
        scenario_id="wrong_speaker_strict_social_emission",
        debug_context=debug_context,
    )
    if "final_emitted_source" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
            turn,
            protected_social_supplemental_structural_expectation(
                require_present=("final_emitted_source",),
            ),
            scenario_id="wrong_speaker_strict_social_emission",
            debug_context=debug_context,
        )


def test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants(monkeypatch):
    session, world, scene_id, resolution = runner_strict_bundle()
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
    patch_get_speaker_selection_contract(monkeypatch, locked_runner_contract())
    pre_gate_line = 'Ragged stranger says, "No names, only rumors."'
    patch_build_final_strict_social_response(
        monkeypatch, line=pre_gate_line, strict_social_details=stub_strict_social_details
    )

    out, _ = apply_final_emission_gate_consumer(
        {"player_facing_text": pre_gate_line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=scene_id,
        world=world,
    )

    final_text = str(out.get("player_facing_text") or "")
    meta = read_fem_meta_from_gate_output(out) or {}
    npc_id = (resolution.get("social") or {}).get("npc_id")
    turn = observed_turn_from_gate_output(
        scenario_id="declared_alias_dialogue_plan",
        gm_output=out,
        resolution=resolution,
        extra_fields={
            "trace": {
                "canonical_entry": {
                    "target_actor_id": npc_id,
                    "declared_alias_target_actor_id": npc_id,
                    "allowed_pregate_speaker_labels": ["Ragged stranger"],
                    "speaker_alias_resolution_source": "manual_bundle_override",
                }
            },
            "dialogue_plan_valid": meta.get("dialogue_plan_valid"),
        },
        unavailable=["fallback_family"],
    )

    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
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
        ),
        scenario_id="declared_alias_dialogue_plan",
        debug_context=f"meta={meta!r}; final_text={final_text!r}",
    )


def test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response("The scene pauses without offering anything concrete."),
        suppress_exploration=False,
        suppress_intent=False,
    )

    result = run_golden_replay(
        scenario_id="thin_answer_action_outcome_final_emission",
        turns=["I examine the notice board; does it show where the missing patrol went?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_scene_object_investigation_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    low = str(turn.get("final_text") or "").lower()
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_structural_expectation(
            require_present=("final_text", "final_emitted_source"),
            allow_unavailable=(
                "fallback_family",
                "selected_speaker_id",
                "trace.canonical_entry",
                "trace.social_contract_trace",
            ),
            equals={
                "response_type_required": "action_outcome",
                "response_type_repair_used": True,
            },
            include_route_kind=False,
            disallow_global_scene_fallback=True,
            extra_no_scaffold_terms=(
                "scene pauses",
                "nothing concrete",
                "no name comes clear",
            ),
        ),
        scenario_id="thin_answer_action_outcome_final_emission",
        debug_context=debug_context,
    )
    assert "patrol" in low or "east ridge" in low or "notice" in low, debug_context
    assert turn.get("sanitizer_lineage_legacy_rewrite_active") is not True


def test_golden_replay_sanitizer_scaffold_leakage_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response(
            "Planner: route via router. Validator: unresolved scaffold."
        ),
    )

    result = run_golden_replay(
        scenario_id="sanitizer_scaffold_leakage",
        turns=["Where should I start?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_scene_object_investigation_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    assert turn.get("sanitizer_lineage_legacy_rewrite_active") is not True
    assert_protected_golden_turn_observation(
        turn,
        protected_structural_expectation(
            require_present=("final_text",),
            allow_unavailable=(
                "fallback_family",
                "final_emitted_source",
                "selected_speaker_id",
                "trace.canonical_entry",
                "trace.social_contract_trace",
            ),
            include_route_kind=False,
            extra_no_scaffold_terms=("Planner", "Validator"),
        ),
        scenario_id="sanitizer_scaffold_leakage",
        debug_context=format_golden_replay_debug(result),
    )
    if "final_emitted_source" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
            turn,
            protected_social_supplemental_structural_expectation(
                require_present=("final_emitted_source",),
                allow_unavailable=(
                    "fallback_family",
                    "selected_speaker_id",
                    "trace.canonical_entry",
                    "trace.social_contract_trace",
                ),
            ),
            scenario_id="sanitizer_scaffold_leakage",
            debug_context=format_golden_replay_debug(result),
        )


def test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership():
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out, _ = apply_final_emission_gate_consumer(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    final_text = str(out.get("player_facing_text") or "")
    meta = read_fem_meta_from_gate_output(out) or {}
    turn = observed_turn_from_gate_output(
        scenario_id="opening_fallback_path",
        gm_output=out,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        unavailable=[],
    )

    assert_protected_golden_turn_observation(
        turn,
        protected_structural_expectation(
            require_present=(
                "final_text",
                "final_emitted_source",
                "fallback_family",
                "opening_fallback_owner_bucket",
            ),
            equals=successful_opening_observed_fields(
                include_owner_bucket=True,
                response_type_required="scene_opening",
                response_type_repair_used=True,
            ),
            not_equals={
                "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
            },
            include_route_kind=False,
        ),
        scenario_id="opening_fallback_path",
        debug_context=f"meta={meta!r}; final_text={final_text!r}",
    )
    assert turn["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    assert turn["opening_fallback_authorship_source"] != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert meta.get("fallback_family_used") == OPENING_FALLBACK_FAMILY
    assert meta.get("realization_fallback_family") == "upstream_prepared_emission"
    assert meta.get("realization_fallback_family") != "legacy_diegetic_fallback"
    assert meta.get("fallback_family_used") != meta.get("realization_fallback_family")


def test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants(tmp_path, monkeypatch):
    responses = iter(
        [
            gm_response(
                'Tavern Runner says, "The patrol never came back from the old milestone beyond the east road."'
            ),
            gm_response('Tavern Runner says, "Last reliable sign was the old milestone."'),
        ]
    )

    def _fake_call_gpt(_messages):
        return next(responses)

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="lead_followup_with_dialogue_lock",
        turns=[
            "Tavern Runner, what happened to the patrol?",
            "Runner, where were they last seen?",
        ],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_tavern_patrol_lead_world,
    )

    assert result["turn_count"] == 2
    turn = result["turns"][1]
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
            selected_speaker_id="tavern_runner",
            require_final_emitted_source=True,
            include_trace_route=True,
        ),
        scenario_id="lead_followup_with_dialogue_lock",
        debug_context=debug_context,
    )
    canonical_entry = (turn.get("trace") or {}).get("canonical_entry") or {}
    if canonical_entry:
        assert_protected_golden_turn_observation(
            turn,
            protected_social_trace_target_expectation("tavern_runner"),
            scenario_id="lead_followup_with_dialogue_lock",
            debug_context=debug_context,
        )


def test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability(tmp_path, monkeypatch):
    fixture = frontier_gate_branch_replay_fixture("branch_social_inquiry")
    turns = fixture["player_prompts"]
    turn_ids = fixture["turn_ids"]
    spine = fixture["spine"]
    assert len(turns) == 25

    gpt_call_count = 0

    def _fake_call_gpt(_messages):
        nonlocal gpt_call_count
        gpt_call_count += 1
        return gm_response(
            (
                "The gate inquiry stays anchored: the notice board, Captain Thoran, the Ash Compact census "
                "delay, muddy footprints northwest of the crates, and the missing patrol route remain in view. "
                f"The answer advances the same thread at deterministic call {gpt_call_count}."
            )
        )

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="frontier_gate_social_inquiry_25_turn",
        turns=turns,
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_frontier_gate_world,
        starting_scene_id="frontier_gate",
        source_path=fixture["source_path"],
        branch_id=fixture["branch_id"],
        turn_ids=turn_ids,
    )

    observed_turns = result["turns"]
    assert observed_turns[0]["source_path"] == fixture["source_path"]
    assert observed_turns[0]["branch_id"] == fixture["branch_id"]
    assert observed_turns[0]["turn_id"] == "inv_01"
    assert observed_turns[-1]["turn_id"] == "inv_25"
    summary = summarize_long_session_replay_observations(observed_turns)
    continuity_bridge = evaluate_golden_replay_continuity_drift(
        spine=spine,
        branch_id=fixture["branch_id"],
        turns=observed_turns,
        turn_ids=turn_ids,
    )
    continuity_eval = continuity_bridge["evaluation"]
    summary["continuity_drift"] = continuity_eval
    debug_context = "\n\n".join(
        [
            format_golden_replay_debug(result),
            render_long_session_replay_summary_markdown(
                scenario_id="frontier_gate_social_inquiry_25_turn",
                turns=observed_turns,
                summary=summary,
                title="Golden Replay 25-Turn Structural Stability",
            ),
        ]
    )
    assert f"source_path: {fixture['source_path']!r}" in debug_context
    assert f"branch_id: {fixture['branch_id']!r}" in debug_context
    assert "turn_id: 'inv_01'" in debug_context

    assert_golden_replay_profile_bundle(
        result=result,
        turns=observed_turns,
        summary=summary,
        continuity_eval=continuity_eval,
        stability_expected=FRONTIER_GATE_SOCIAL_INQUIRY_STABILITY_PROFILE,
        lineage_expected=FRONTIER_GATE_SOCIAL_INQUIRY_LINEAGE_PROFILE,
        fallback_escalation_expected=FRONTIER_GATE_SOCIAL_INQUIRY_FALLBACK_ESCALATION_PROFILE,
        debug_context=debug_context,
    )


def test_golden_replay_frontier_gate_social_inquiry_25_turn_resume_persistence_supporting(tmp_path, monkeypatch):
    # Supporting checkpoint probe: this uses a real on-disk snapshot restore at
    # the 12/13 boundary, but keeps the protected lock on the uninterrupted run.
    fixture = frontier_gate_branch_replay_fixture("branch_social_inquiry")
    turns = fixture["player_prompts"]
    turn_ids = fixture["turn_ids"]
    spine = fixture["spine"]
    split_at = 12
    assert len(turns) == 25
    assert turn_ids[split_at - 1] == "inv_12"
    assert turn_ids[split_at] == "inv_13"

    gpt_call_count = 0

    def _fake_call_gpt(_messages):
        nonlocal gpt_call_count
        gpt_call_count += 1
        return gm_response(
            (
                "The resumed gate inquiry stays anchored: the notice board, Captain Thoran, "
                "the Ash Compact census delay, muddy footprints northwest of the crates, "
                "and the missing patrol route remain in view. "
                f"The answer advances the same thread at deterministic call {gpt_call_count}."
            )
        )

    observed_turns = []
    checkpoint_meta = None
    restored_meta = None
    pre_resume_counter = None
    post_restore_counter = None
    post_restore_log_count = None

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    new_clean_campaign(starting_scene_id="frontier_gate")
    seed_frontier_gate_world()

    for i, text in enumerate(turns[:split_at]):
        payload = chat(ChatRequest(text=text))
        snap = snapshot_from_chat_payload(i, text, payload)
        observed_turns.append(
            _observed_turn(
                scenario_id="frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
                snap=snap,
                payload=payload,
                replay_identity={
                    "source_path": fixture["source_path"],
                    "branch_id": fixture["branch_id"],
                    "turn_id": turn_ids[i],
                },
            )
        )

    pre_resume_counter = int(storage.load_session().get("turn_counter") or 0)
    checkpoint_meta = storage.create_snapshot(label="golden-social-inquiry-after-turn-12")
    restored_meta = storage.load_snapshot(str(checkpoint_meta["id"]))
    post_restore_session = storage.load_session()
    post_restore_counter = int(post_restore_session.get("turn_counter") or 0)
    post_restore_log_count = len(storage.load_log())

    for i, text in enumerate(turns[split_at:], start=split_at):
        payload = chat(ChatRequest(text=text))
        snap = snapshot_from_chat_payload(i, text, payload)
        observed_turns.append(
            _observed_turn(
                scenario_id="frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
                snap=snap,
                payload=payload,
                replay_identity={
                    "source_path": fixture["source_path"],
                    "branch_id": fixture["branch_id"],
                    "turn_id": turn_ids[i],
                },
            )
        )

    result = {
        "scenario_id": "frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
        "turn_count": len(observed_turns),
        "turns": observed_turns,
    }
    pre_resume_turns = observed_turns[:split_at]
    post_resume_turns = observed_turns[split_at:]
    summary = summarize_long_session_replay_observations(observed_turns)
    pre_summary = summarize_long_session_replay_observations(pre_resume_turns)
    post_summary = summarize_long_session_replay_observations(post_resume_turns)
    continuity_bridge = evaluate_golden_replay_continuity_drift(
        spine=spine,
        branch_id=fixture["branch_id"],
        turns=observed_turns,
        turn_ids=turn_ids,
    )
    continuity_eval = continuity_bridge["evaluation"]
    summary["continuity_drift"] = continuity_eval
    debug_context = "\n\n".join(
        [
            f"split_at: {split_at}",
            f"checkpoint_meta: {checkpoint_meta!r}",
            f"restored_meta: {restored_meta!r}",
            f"pre_resume_counter: {pre_resume_counter!r}",
            f"post_restore_counter: {post_restore_counter!r}",
            f"post_restore_log_count: {post_restore_log_count!r}",
            f"pre_resume_summary: {pre_summary!r}",
            f"post_resume_summary: {post_summary!r}",
            format_golden_replay_debug(result),
            render_long_session_replay_summary_markdown(
                scenario_id="frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
                turns=observed_turns,
                summary=summary,
                title="Golden Replay 25-Turn Resume Persistence Supporting Probe",
            ),
        ]
    )

    assert checkpoint_meta is not None, debug_context
    assert restored_meta is not None, debug_context
    assert pre_resume_counter == split_at, debug_context
    assert post_restore_counter == split_at, debug_context
    assert post_restore_log_count == split_at, debug_context
    assert storage.load_session().get("turn_counter") == 25, debug_context
    assert len(storage.load_log()) == 25, debug_context

    assert result["turn_count"] == 25, debug_context
    assert summary["turn_count"] == 25, debug_context
    assert [turn.get("turn_index") for turn in observed_turns] == list(range(25)), debug_context
    assert [turn.get("turn_id") for turn in observed_turns] == turn_ids, debug_context
    assert observed_turns[split_at - 1]["turn_id"] == "inv_12", debug_context
    assert observed_turns[split_at]["turn_id"] == "inv_13", debug_context
    assert observed_turns[0]["source_path"] == fixture["source_path"]
    assert observed_turns[0]["branch_id"] == fixture["branch_id"]
    assert observed_turns[-1]["turn_id"] == "inv_25"

    assert pre_summary["turn_count"] == split_at, debug_context
    assert post_summary["turn_count"] == 25 - split_at, debug_context
    assert pre_summary["speaker_missing_count"] <= 2, debug_context
    assert post_summary["speaker_missing_count"] <= 1, debug_context
    assert observed_turns[split_at]["selected_speaker_id"] is not None, debug_context
    assert observed_turns[split_at]["selected_speaker_source"] is not None, debug_context
    assert_golden_replay_profile_bundle(
        result=result,
        turns=observed_turns,
        summary=summary,
        continuity_eval=continuity_eval,
        stability_expected=FRONTIER_GATE_RESUME_STABILITY_PROFILE,
        lineage_expected=FRONTIER_GATE_RESUME_LINEAGE_PROFILE,
        fallback_escalation_expected=FRONTIER_GATE_RESUME_FALLBACK_ESCALATION_PROFILE,
        debug_context=debug_context,
    )


def test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability(tmp_path, monkeypatch):
    # Supporting diagnostic only: this branch intentionally stresses risky
    # action/visibility paths and currently emits more fallback lineage than the
    # protected social-inquiry baseline. Keep it supporting until it gets another
    # clean run after future fallback-family or action-routing changes.
    fixture = frontier_gate_branch_replay_fixture("branch_direct_intrusion")
    turns = fixture["player_prompts"]
    turn_ids = fixture["turn_ids"]
    spine = fixture["spine"]
    assert len(turns) == 25

    gpt_call_count = 0

    def _fake_call_gpt(_messages):
        nonlocal gpt_call_count
        gpt_call_count += 1
        return gm_response(
            (
                "The direct intrusion stays anchored: the gate serjeant, roster board, cordon pressure, "
                "warehouse latch, muddy crates, and watch whistles remain in view. "
                f"The risky push advances the same forced-access thread at deterministic call {gpt_call_count}."
            )
        )

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="frontier_gate_direct_intrusion_25_turn_diagnostic",
        turns=turns,
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_frontier_gate_world,
        starting_scene_id="frontier_gate",
        source_path=fixture["source_path"],
        branch_id=fixture["branch_id"],
        turn_ids=turn_ids,
    )

    observed_turns = result["turns"]
    assert observed_turns[0]["source_path"] == fixture["source_path"]
    assert observed_turns[0]["branch_id"] == fixture["branch_id"]
    assert observed_turns[0]["turn_id"] == "act_01"
    assert observed_turns[-1]["turn_id"] == "act_25"
    summary = summarize_long_session_replay_observations(observed_turns)
    continuity_bridge = evaluate_golden_replay_continuity_drift(
        spine=spine,
        branch_id=fixture["branch_id"],
        turns=observed_turns,
        turn_ids=turn_ids,
    )
    continuity_eval = continuity_bridge["evaluation"]
    summary["continuity_drift"] = continuity_eval
    debug_context = "\n\n".join(
        [
            format_golden_replay_debug(result),
            render_long_session_replay_summary_markdown(
                scenario_id="frontier_gate_direct_intrusion_25_turn_diagnostic",
                turns=observed_turns,
                summary=summary,
                title="Golden Replay 25-Turn Direct-Intrusion Diagnostic Stability",
            ),
        ]
    )
    assert f"source_path: {fixture['source_path']!r}" in debug_context
    assert f"branch_id: {fixture['branch_id']!r}" in debug_context
    assert "turn_id: 'act_01'" in debug_context

    direct_intrusion_stability_profile = {
        "result_turn_count": 25,
        "summary_equals": {
            "turn_count": 25,
            "fallback_turn_count": 7,
            "fallback_owner_change_count": 0,
        },
        "no_scaffold_leakage": True,
        "summary_max": {
            "route_change_count": 6,
            "speaker_change_count": 3,
            "speaker_missing_count": 20,
            "mutation_turn_count": 25,
        },
        "session_health": {
            "equals": {"long_session_band": "long", "overall_passed": True},
            "classification_in": {"clean", "warning"},
        },
        "degradation": {
            "equals": {"progressive_degradation_detected": False},
            "absent_reason_codes": {
                "late_session_reset_or_amnesia",
                "rising_generic_filler_strong",
                "rising_generic_filler_progressive",
                "debug_leak_late_window",
                "referent_loss_late",
                "continuity_anchor_late_loss",
            },
        },
        "continuity_axes_passed": {"narrative_grounding", "branch_coherence"},
    }

    fallback_frequency = summary["fallback_frequency"]
    assert set(fallback_frequency) <= {
        NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
        "gate_terminal_repair",
    }, debug_context
    assert int(fallback_frequency.get(NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY) or 0) <= 4, debug_context
    assert int(fallback_frequency.get("gate_terminal_repair") or 0) <= 3, debug_context
    direct_intrusion_fallback_escalation_profile = {
        "equals": {
            "fallback_total_count": 7,
            "max_blocking_fallback_streak": 0,
            "fallback_owner_change_count": 0,
            "fallback_lineage_owner_change_count": 0,
            "fallback_behavior_repair_count": 0,
            "sanitizer_fallback_count": 0,
            "scene_action_speaker_optional_unavailable_count": 7,
            "blocking_unavailable_with_fallback_count": 0,
            "fallback_selected_without_family_count": 0,
            "escalation_warnings": [],
            "model_routing_escalation_observable": False,
        },
        "max": {
            "max_fallback_streak": 2,
            "max_scene_action_nonblocking_fallback_streak": 2,
            "late_window_fallback_count": 2,
            "response_type_repair_count": 2,
            "unavailable_with_fallback_count": 7,
        },
        "allowed_fallback_families": {
            NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            "gate_terminal_repair",
        },
        "fallback_family_counts": {
            NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY: 4,
            "gate_terminal_repair": 3,
        },
    }
    assert_golden_replay_profile_bundle(
        result=result,
        turns=observed_turns,
        summary=summary,
        continuity_eval=continuity_eval,
        stability_expected=direct_intrusion_stability_profile,
        lineage_expected=FRONTIER_GATE_DIRECT_INTRUSION_LINEAGE_PROFILE,
        fallback_escalation_expected=direct_intrusion_fallback_escalation_profile,
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
        return gm_response('Tavern Runner says, "The east road keeps the best clue."')

    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=_fake_call_gpt,
        suppress_exploration=False,
        suppress_intent=False,
    )

    branch_rows: list[dict] = []
    for branch in spine.branches:
        result = run_golden_replay(
            scenario_id=f"scenario_spine_three_branch::{branch.branch_id}",
            turns=[turn.player_prompt for turn in branch.turns],
            tmp_path=tmp_path / branch.branch_id,
            monkeypatch=monkeypatch,
            setup_fn=seed_spine_three_branch_world,
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
                    **protected_structural_expectation(
                        require_present=("final_text",),
                        allow_unavailable=(
                            "fallback_family",
                            "selected_speaker_id",
                            "final_emitted_source",
                            "trace.canonical_entry",
                            "trace.social_contract_trace",
                        ),
                        no_scaffold=False,
                        include_route_kind=False,
                    ),
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
