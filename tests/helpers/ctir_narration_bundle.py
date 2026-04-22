"""Non-production helpers: align narration plan bundle with manually attached CTIR in unit tests."""

from __future__ import annotations

from typing import Any

from game.ctir_runtime import SESSION_CTIR_STAMP_KEY
from game.narration_plan_bundle import build_narration_plan_bundle, ensure_narration_plan_bundle_for_turn


def ensure_narration_plan_bundle_for_manual_ctir_tests(
    session: dict[str, Any],
    narration_context_kwargs: dict[str, Any],
) -> str:
    """Attach a stamp-matched narration plan bundle (outside the production API seam)."""
    stamp = str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip()
    if not stamp:
        stamp = "non_production_test_ctir_bundle_stamp_v1"
        session[SESSION_CTIR_STAMP_KEY] = stamp
    merged = {**narration_context_kwargs, "session": session}
    ensure_narration_plan_bundle_for_turn(
        session,
        turn_stamp=stamp,
        builder=lambda: build_narration_plan_bundle(session=session, narration_context_kwargs=merged),
    )
    return stamp
