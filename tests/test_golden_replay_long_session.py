"""Long-session golden replay stability/profile coverage.

This file owns long-session golden replay stability/profile coverage.
Profile constants remain in tests/helpers/golden_replay_profiles.py.
Replay orchestration remains in tests/helpers/golden_replay.py.
"""

from __future__ import annotations

from game import storage
from game.api import chat
from game.models import ChatRequest
from tests.helpers.golden_replay import (
    _observed_turn,
    assert_golden_replay_profile_bundle,
    evaluate_golden_replay_continuity_drift,
    format_golden_replay_debug,
    frontier_gate_branch_replay_fixture,
    render_long_session_replay_summary_markdown,
    run_golden_replay,
    summarize_long_session_replay_observations,
)
from tests.helpers.golden_replay_profiles import (
    FRONTIER_GATE_DIRECT_INTRUSION_FALLBACK_ESCALATION_PROFILE,
    FRONTIER_GATE_DIRECT_INTRUSION_LINEAGE_PROFILE,
    FRONTIER_GATE_DIRECT_INTRUSION_STABILITY_PROFILE,
    FRONTIER_GATE_RESUME_FALLBACK_ESCALATION_PROFILE,
    FRONTIER_GATE_RESUME_LINEAGE_PROFILE,
    FRONTIER_GATE_RESUME_STABILITY_PROFILE,
    FRONTIER_GATE_SOCIAL_INQUIRY_FALLBACK_ESCALATION_PROFILE,
    FRONTIER_GATE_SOCIAL_INQUIRY_LINEAGE_PROFILE,
    FRONTIER_GATE_SOCIAL_INQUIRY_STABILITY_PROFILE,
)
from tests.helpers.transcript_runner import (
    new_clean_campaign,
    patch_transcript_storage,
    snapshot_from_chat_payload,
    write_default_bootstrap_scenes,
)
from tests.helpers.golden_replay_fixtures import (
    gm_response,
    golden_replay_chat_stubs,
    seed_frontier_gate_world,
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

    assert_golden_replay_profile_bundle(
        result=result,
        turns=observed_turns,
        summary=summary,
        continuity_eval=continuity_eval,
        stability_expected=FRONTIER_GATE_DIRECT_INTRUSION_STABILITY_PROFILE,
        lineage_expected=FRONTIER_GATE_DIRECT_INTRUSION_LINEAGE_PROFILE,
        fallback_escalation_expected=FRONTIER_GATE_DIRECT_INTRUSION_FALLBACK_ESCALATION_PROFILE,
        debug_context=debug_context,
    )
