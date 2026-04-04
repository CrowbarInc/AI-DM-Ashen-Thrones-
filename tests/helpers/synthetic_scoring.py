"""Synthetic-player infrastructure for tests/tooling only. No production imports from this module."""

from __future__ import annotations

from collections import Counter
from typing import Any

from tests.helpers.synthetic_types import SyntheticRunResult

_KNOWN_STOP_REASONS = {
    "max_turns_reached",
    "stall_repeat_threshold",
    "policy_stop",
    "external_stop",
}
_CLUE_LIKE_TOKENS = ("clue", "mark", "observation", "notice", "spot", "evidence", "hint")


def _normalized(text: Any) -> str:
    return str(text or "").strip().lower()


def _turn_views(run_result: SyntheticRunResult) -> tuple[dict[str, Any], ...]:
    return tuple(run_result.turn_views or ())


def _window_has_low_variation(values: list[str], *, window: int) -> bool:
    if window <= 0 or len(values) < window:
        return False
    for idx in range(window - 1, len(values)):
        span = values[idx - window + 1 : idx + 1]
        non_empty = [value for value in span if value]
        if non_empty and len(set(non_empty)) <= 1:
            return True
    return False


def detect_soft_lock(
    run_result: SyntheticRunResult,
    *,
    repeat_window: int = 3,
    low_variation_window: int = 4,
) -> dict[str, Any]:
    """Return a lightweight soft-lock diagnosis from compact turn views."""
    views = _turn_views(run_result)
    player_texts = [_normalized(view.get("player_text")) for view in views]
    gm_texts = [_normalized(view.get("gm_text")) for view in views]
    reasons: list[str] = []

    if str(run_result.stop_reason).strip() == "stall_repeat_threshold":
        reasons.append("stop_reason=stall_repeat_threshold")
    if _window_has_low_variation(player_texts, window=repeat_window):
        reasons.append(f"player_text_repeats_window={repeat_window}")
    if _window_has_low_variation(gm_texts, window=repeat_window):
        reasons.append(f"gm_text_repeats_window={repeat_window}")

    pairs = [f"{p}|{g}" for p, g in zip(player_texts, gm_texts, strict=False)]
    if _window_has_low_variation(pairs, window=low_variation_window):
        reasons.append(f"no_visible_progress_window={low_variation_window}")

    return {
        "is_soft_lock": bool(reasons),
        "reasons": tuple(reasons),
        "repeat_window": repeat_window,
        "low_variation_window": low_variation_window,
    }


def count_meaningful_progress_signals(run_result: SyntheticRunResult) -> dict[str, int]:
    """Count compact, explainable progress indicators from turn views."""
    views = _turn_views(run_result)
    player_texts = [_normalized(view.get("player_text")) for view in views]
    gm_texts = [_normalized(view.get("gm_text")) for view in views]
    scene_ids = [_normalized(view.get("scene_id")) for view in views]
    rationales = [_normalized(view.get("decision_rationale")) for view in views]

    clue_like_count = sum(
        1 for text in gm_texts if text and any(token in text for token in _CLUE_LIKE_TOKENS)
    )
    scene_change_count = sum(1 for left, right in zip(scene_ids, scene_ids[1:], strict=False) if left != right)
    rationale_change_count = sum(
        1 for left, right in zip(rationales, rationales[1:], strict=False) if left != right
    )
    non_stall_stop = int(_normalized(run_result.stop_reason) not in {"", "stall_repeat_threshold"})
    recognized_stop = int(_normalized(run_result.stop_reason) in _KNOWN_STOP_REASONS)

    return {
        "turn_count": len(views),
        "non_empty_player_turns": sum(1 for text in player_texts if text),
        "non_empty_gm_turns": sum(1 for text in gm_texts if text),
        "unique_player_inputs": len({text for text in player_texts if text}),
        "unique_gm_outputs": len({text for text in gm_texts if text}),
        "rationale_changes": rationale_change_count,
        "scene_changes": scene_change_count,
        "clue_like_responses": clue_like_count,
        "recognized_stop_reason": recognized_stop,
        "non_stall_stop_reason": non_stall_stop,
    }


def summarize_synthetic_run(run_result: SyntheticRunResult) -> str:
    """Build a concise, actionable debug summary for assertion failures."""
    signals = count_meaningful_progress_signals(run_result)
    soft_lock = detect_soft_lock(run_result)
    views = _turn_views(run_result)
    player_texts = [_normalized(view.get("player_text")) for view in views]
    gm_texts = [_normalized(view.get("gm_text")) for view in views]

    top_player = Counter(text for text in player_texts if text).most_common(2)
    top_gm = Counter(text for text in gm_texts if text).most_common(2)
    soft_lock_text = ",".join(soft_lock["reasons"]) if soft_lock["reasons"] else "none"

    return (
        f"profile={run_result.profile_name!r} seed={run_result.seed} stop={run_result.stop_reason!r} "
        f"turns={signals['turn_count']} "
        f"player_non_empty={signals['non_empty_player_turns']}/{signals['turn_count']} "
        f"gm_non_empty={signals['non_empty_gm_turns']}/{signals['turn_count']} "
        f"player_unique={signals['unique_player_inputs']} gm_unique={signals['unique_gm_outputs']} "
        f"clue_like={signals['clue_like_responses']} "
        f"soft_lock={soft_lock['is_soft_lock']}[{soft_lock_text}] "
        f"top_player={top_player} top_gm={top_gm}"
    )


def score_synthetic_run(run_result: SyntheticRunResult) -> dict[str, Any]:
    """Small convenience wrapper for callers that want one object."""
    return {
        "progress": count_meaningful_progress_signals(run_result),
        "soft_lock": detect_soft_lock(run_result),
        "summary": summarize_synthetic_run(run_result),
    }


def score_placeholder_turns(*, turn_count: int = 0) -> float:
    """Back-compat helper retained for older scaffolding tests."""
    return float(max(0, int(turn_count)))
