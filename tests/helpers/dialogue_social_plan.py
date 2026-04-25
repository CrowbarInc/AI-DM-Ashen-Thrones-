"""Shared helpers for constructing/attaching valid dialogue_social_plan fixtures in tests.

These helpers intentionally keep invalid-plan construction explicit at call sites: use
`make_valid_dialogue_social_plan()` for valid fixtures, then mutate locally when testing
specific validation failures.
"""

from __future__ import annotations

from typing import Any, Mapping

from game.dialogue_social_plan import validate_dialogue_social_plan


def make_valid_dialogue_social_plan(
    *,
    speaker_id: str = "npc_x",
    speaker_name: str = "NPC X",
    dialogue_intent: str = "question",
    reply_kind: str = "answer",
    pressure_state: str = "low",
    relationship_codes: list[str] | None = None,
    tone_bounds: list[str] | None = None,
    speaker_source: str = "tests.helpers.dialogue_social_plan",
    prohibited_content_codes: list[str] | None = None,
    derivation_codes: list[str] | None = None,
    applies: bool = True,
    **overrides: Any,
) -> dict[str, Any]:
    """Return a minimal valid dialogue_social_plan dict (structural-only).

    - Uses the real `validate_dialogue_social_plan` contract check.
    - Defaults avoid generating any dialogue/prompt text.
    - Callers can override any field via kwargs, but this helper should be used only for
      constructing *valid* plans (mutate locally for invalid-plan tests).
    """

    plan: dict[str, Any] = {
        "version": 1,
        "applies": bool(applies),
        "speaker_id": speaker_id if applies else (speaker_id or None),
        "speaker_name": speaker_name if speaker_name else None,
        "speaker_source": speaker_source,
        "dialogue_intent": dialogue_intent if applies else (dialogue_intent or None),
        "reply_kind": reply_kind,
        "pressure_state": pressure_state,
        "relationship_codes": list(relationship_codes) if relationship_codes is not None else ["unknown"],
        "tone_bounds": list(tone_bounds) if tone_bounds is not None else ["neutral"],
        "prohibited_content_codes": list(prohibited_content_codes)
        if prohibited_content_codes is not None
        else [
            "no_narrator_override",
            "no_ooc_instructions",
            "no_player_agency_override",
            "no_prompt_text",
        ],
        "derivation_codes": list(derivation_codes) if derivation_codes is not None else ["dialogue_social_plan:v1", "intent:ctir_only"],
        # Keep validator minimal; validate_dialogue_social_plan will populate it.
        "validator": {"validated": False, "errors": []},
    }

    if overrides:
        plan.update(overrides)

    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is True, errs
    return plan


def attach_dialogue_social_plan_to_resolution(
    resolution: dict[str, Any],
    plan: Mapping[str, Any],
    *,
    path: tuple[str, ...] = ("metadata", "emission_debug", "dialogue_social_plan"),
) -> dict[str, Any]:
    """Attach `plan` into a resolution at the usual emission_debug location."""

    cur: dict[str, Any] = resolution
    for key in path[:-1]:
        nxt = cur.get(key)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[key] = nxt
        cur = nxt
    cur[path[-1]] = dict(plan)
    return resolution


def assert_valid_dialogue_social_plan(plan: Mapping[str, Any]) -> None:
    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is True, errs

