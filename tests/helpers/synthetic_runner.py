"""Synthetic-player infrastructure for tests/tooling only. No production imports from this module."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tests.helpers.synthetic_profiles import default_placeholder_profile
from tests.helpers.synthetic_types import SyntheticDecision, SyntheticRunResult


def run_placeholder_session(
    *,
    max_turns: int = 0,
    profile: Any | None = None,
    seed: int = 0,
    player_texts: tuple[str, ...] = (),
    use_fake_gm: bool = False,
    fake_gm_responder: Any | None = None,
    monkeypatch: Any | None = None,
    fake_gm_patch_targets: tuple[str, ...] = (),
    tmp_path: Any | None = None,
    starting_scene_id: str | None = None,
    extra_scene_ids: tuple[str, ...] = (),
    stall_repeat_threshold: int = 3,
    policy_fn: Callable[[Any], SyntheticDecision] | None = None,
    stop_predicate: Callable[[SyntheticRunResult], bool] | None = None,
) -> SyntheticRunResult:
    """Compatibility wrapper for the real synthetic session runner."""
    return run_synthetic_session(
        max_turns=max_turns,
        profile=profile,
        seed=seed,
        player_texts=player_texts,
        use_fake_gm=use_fake_gm,
        fake_gm_responder=fake_gm_responder,
        monkeypatch=monkeypatch,
        fake_gm_patch_targets=fake_gm_patch_targets,
        tmp_path=tmp_path,
        starting_scene_id=starting_scene_id,
        extra_scene_ids=extra_scene_ids,
        stall_repeat_threshold=stall_repeat_threshold,
        policy_fn=policy_fn,
        stop_predicate=stop_predicate,
    )


def _decision_requests_stop(decision: SyntheticDecision) -> tuple[bool, str]:
    stop_requested = bool(getattr(decision, "stop_requested", False))
    if stop_requested:
        reason = str(getattr(decision, "stop_reason", "")).strip() or "policy_stop"
        return True, reason
    return False, ""


def _compact_turn_view(turn_index: int, decision: SyntheticDecision, snapshot: dict[str, Any]) -> dict[str, Any]:
    gm_text = ""
    if isinstance(snapshot.get("gm_text"), str):
        gm_text = snapshot["gm_text"]
    elif isinstance(snapshot.get("response"), dict):
        gm_text = str(snapshot["response"].get("player_facing_text") or "")

    return {
        "turn_index": turn_index,
        "player_text": decision.player_text,
        "decision_rationale": decision.rationale,
        "gm_text": gm_text,
        "scene_id": snapshot.get("scene_id"),
        "raw_snapshot": snapshot,
    }


def run_synthetic_session(
    *,
    max_turns: int = 0,
    profile: Any | None = None,
    seed: int = 0,
    player_texts: tuple[str, ...] = (),
    use_fake_gm: bool = False,
    fake_gm_responder: Any | None = None,
    monkeypatch: Any | None = None,
    fake_gm_patch_targets: tuple[str, ...] = (),
    tmp_path: Any | None = None,
    starting_scene_id: str | None = None,
    extra_scene_ids: tuple[str, ...] = (),
    stall_repeat_threshold: int = 3,
    policy_fn: Callable[[Any], SyntheticDecision] | None = None,
    stop_predicate: Callable[[SyntheticRunResult], bool] | None = None,
) -> SyntheticRunResult:
    """Run a deterministic synthetic session with lazy transcript/game integration."""
    profile_obj = profile or default_placeholder_profile()
    turn_count = max(0, int(max_turns))
    seed_value = int(seed)
    effective_policy_fn = policy_fn
    if effective_policy_fn is None:
        # Lazy import keeps module import thin and free of production/runtime coupling.
        from tests.helpers.synthetic_policy import decide_placeholder

        effective_policy_fn = decide_placeholder

    if use_fake_gm:
        # Lazy import keeps module import thin and free of production/runtime coupling.
        from tests.helpers.synthetic_fake_gm import (
            build_fake_gm_snapshot,
            install_fake_responder_monkeypatches,
            make_deterministic_fake_responder,
        )
        from tests.helpers.synthetic_types import SyntheticTurnView

        active_responder = fake_gm_responder or make_deterministic_fake_responder()
        if monkeypatch is not None and fake_gm_patch_targets:
            active_responder = install_fake_responder_monkeypatches(
                monkeypatch=monkeypatch,
                target_paths=fake_gm_patch_targets,
                responder=active_responder,
            )

        decisions: list[SyntheticDecision] = []
        snapshots: list[dict[str, Any]] = []
        turn_views: list[dict[str, Any]] = []
        history: list[str] = []
        stop_reason = "max_turns_reached"

        for turn_index in range(turn_count):
            if turn_index < len(player_texts) and str(player_texts[turn_index]).strip():
                decision = SyntheticDecision(player_text=str(player_texts[turn_index]).strip(), rationale="provided")
            else:
                view = SyntheticTurnView(
                    turn_index=turn_index,
                    player_text_history=tuple(history),
                    snapshot=(snapshots[-1] if snapshots else None),
                    seed=seed_value,
                    profile=profile_obj,
                )
                decision = effective_policy_fn(view)
                text = str(getattr(decision, "player_text", "")).strip()
                if not text:
                    decision = SyntheticDecision(player_text="I move the scene forward with one concrete action.", rationale="stall_breaker")

            decisions.append(decision)
            history.append(decision.player_text.strip())
            snapshot = build_fake_gm_snapshot(
                player_text_history=tuple(history),
                responder=active_responder,
            )
            snapshots.append(snapshot)
            turn_views.append(_compact_turn_view(turn_index, decision, snapshot))

            if stop_predicate is not None:
                current = SyntheticRunResult(
                    profiles=(profile_obj,),
                    decisions=tuple(decisions),
                    snapshots=tuple(snapshots),
                    ok=True,
                    profile_name=profile_obj.profile_id,
                    seed=seed_value,
                    stop_reason="",
                    turn_views=tuple(turn_views),
                )
                if stop_predicate(current):
                    stop_reason = "external_stop"
                    break

            if stall_repeat_threshold > 0 and len(history) >= stall_repeat_threshold:
                recent = tuple(text.strip().lower() for text in history[-stall_repeat_threshold:])
                if recent and len(set(recent)) == 1:
                    stop_reason = "stall_repeat_threshold"
                    break

            should_stop, policy_stop_reason = _decision_requests_stop(decision)
            if should_stop:
                stop_reason = policy_stop_reason
                break

        return SyntheticRunResult(
            profiles=(profile_obj,),
            decisions=tuple(decisions),
            snapshots=tuple(snapshots),
            ok=True,
            profile_name=profile_obj.profile_id,
            seed=seed_value,
            stop_reason=stop_reason,
            turn_views=tuple(turn_views),
        )

    # Real transcript/game integration is intentionally lazy and optional.
    from tests.helpers.transcript_runner import run_transcript, run_transcript_turns
    from tests.helpers.synthetic_types import SyntheticTurnView

    decisions = []
    snapshots = []
    turn_views = []
    history = []
    stop_reason = "max_turns_reached"

    for turn_index in range(turn_count):
        if turn_index < len(player_texts) and str(player_texts[turn_index]).strip():
            decision = SyntheticDecision(player_text=str(player_texts[turn_index]).strip(), rationale="provided")
        else:
            view = SyntheticTurnView(
                turn_index=turn_index,
                player_text_history=tuple(history),
                snapshot=(snapshots[-1] if snapshots else None),
                seed=seed_value,
                profile=profile_obj,
            )
            decision = effective_policy_fn(view)
            text = str(getattr(decision, "player_text", "")).strip()
            if not text:
                decision = SyntheticDecision(player_text="I move the scene forward with one concrete action.", rationale="stall_breaker")

        decisions.append(decision)
        history.append(decision.player_text.strip())

        if tmp_path is not None and monkeypatch is not None:
            # run_transcript applies storage patching and campaign reset once for the generated history.
            transcript_snapshots = run_transcript(
                tmp_path,
                monkeypatch,
                list(history),
                starting_scene_id=starting_scene_id,
                extra_scene_ids=extra_scene_ids,
            )
            snapshot = transcript_snapshots[-1]
            snapshots = transcript_snapshots
        else:
            # run_transcript_turns still executes through the chat seam with a clean campaign reset.
            transcript_snapshots = run_transcript_turns(
                list(history),
                starting_scene_id=starting_scene_id,
            )
            snapshot = transcript_snapshots[-1]
            snapshots = transcript_snapshots

        turn_views.append(_compact_turn_view(turn_index, decision, snapshot))

        if stop_predicate is not None:
            current = SyntheticRunResult(
                profiles=(profile_obj,),
                decisions=tuple(decisions),
                snapshots=tuple(snapshots),
                ok=True,
                profile_name=profile_obj.profile_id,
                seed=seed_value,
                stop_reason="",
                turn_views=tuple(turn_views),
            )
            if stop_predicate(current):
                stop_reason = "external_stop"
                break

        if stall_repeat_threshold > 0 and len(history) >= stall_repeat_threshold:
            recent = tuple(text.strip().lower() for text in history[-stall_repeat_threshold:])
            if recent and len(set(recent)) == 1:
                stop_reason = "stall_repeat_threshold"
                break

        should_stop, policy_stop_reason = _decision_requests_stop(decision)
        if should_stop:
            stop_reason = policy_stop_reason
            break

    return SyntheticRunResult(
        profiles=(profile_obj,),
        decisions=tuple(decisions),
        snapshots=tuple(snapshots),
        ok=True,
        profile_name=profile_obj.profile_id,
        seed=seed_value,
        stop_reason=stop_reason,
        turn_views=tuple(turn_views),
    )
