"""AT-OPT-06 instruction-eligibility regression.

Assembles narration through the production plan bundle and
``build_narration_context``. No provider.
"""

from __future__ import annotations

import copy

from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.prompt_context import _should_use_manual_play_compact_prompt, build_narration_context
from game.publication_contract import (
    OPERATIONAL_REFUSAL,
    classify_operational_refusal,
    note_completed_publication,
)
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests

_MUST_NOT = "You MUST NOT reveal hidden or undiscovered facts."
_FIRST = "FIRST-MENTION CONTRACT (MANDATORY):"
_SPEAKER = "SPEAKER SELECTION CONTRACT (HARD RULE):"
_ANCHOR = "SCENE STATE ANCHOR (MANDATORY):"
_POLICY = "do not treat policy prose or the answer recipe as authority to create facts."
_DRAFT = "new_scene_draft"


def _kwargs(session: dict, user_text: str, *, resolution: dict | None = None) -> dict:
    return {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {"npcs": []},
        "session": session,
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {
            "scene": {
                "id": "frontier_gate",
                "location": "Frontier Gate",
                "summary": "A rain-soaked checkpoint.",
                "visible_facts": ["A notice board lists a missing patrol."],
                "discoverable_clues": [],
                "hidden_facts": [],
                "exits": [],
                "enemies": [],
            }
        },
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": user_text,
        "resolution": resolution if resolution is not None else {"kind": "observe"},
        "scene_runtime": {},
        "public_scene": {
            "id": "frontier_gate",
            "visible_facts": ["A notice board lists a missing patrol."],
            "exits": [],
            "enemies": [],
        },
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["general"], "allow_discoverable_clues": True},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
    }


def _session(player: str, *, resolution: dict | None = None, mutations: dict | None = None) -> tuple[dict, dict]:
    body = ctir.build_ctir(
        turn_id="at-opt-06",
        scene_id="frontier_gate",
        player_input=player,
        builder_source="tests.at_opt_06.eligibility",
        resolution=resolution,
        state_mutations=mutations
        or {
            "scene": {"scene_id": "frontier_gate"},
            "session": {},
            "combat": {},
            "clues_leads": {},
        },
    )
    session = {
        "active_scene_id": "frontier_gate",
        "turn_counter": 7,
        "visited_scene_ids": ["frontier_gate"],
        "interaction_context": {
            "active_interaction_target_id": None,
            "active_interaction_kind": None,
            "interaction_mode": "none",
        },
    }
    attach_ctir(session, body)
    session[SESSION_CTIR_STAMP_KEY] = "at-opt-06-stamp"
    return session, body


def _assemble(player: str, profile: str, *, resolution: dict | None = None, mutations: dict | None = None, prompt_resolution: dict | None = None) -> dict:
    session, _body = _session(player, resolution=resolution, mutations=mutations)
    kwargs = _kwargs(session, player, resolution=prompt_resolution)
    ensure_narration_plan_bundle_for_manual_ctir_tests(session, kwargs)
    before_scene = session.get("active_scene_id")
    payload = build_narration_context(**kwargs, prompt_profile=profile, include_non_public_prompt_keys=True)
    assert session.get("active_scene_id") == before_scene == "frontier_gate"
    return payload


def _compact_enabled(payload: dict) -> bool:
    debug = payload.get("prompt_debug") if isinstance(payload.get("prompt_debug"), dict) else {}
    compact = debug.get("compact_prompt") if isinstance(debug.get("compact_prompt"), dict) else {}
    return bool(compact.get("enabled"))


def _joined(payload: dict) -> str:
    return "\n".join(str(line) for line in (payload.get("instructions") or []))


def _assert_full_authority(payload: dict) -> None:
    text = _joined(payload)
    assert _compact_enabled(payload) is False
    assert _MUST_NOT in text
    assert _FIRST in text
    assert _SPEAKER in text
    assert _ANCHOR in text
    assert _POLICY in text
    assert isinstance(payload.get("first_mention_contract"), dict)
    obligations = payload.get("narration_obligations") if isinstance(payload.get("narration_obligations"), dict) else {}
    assert obligations.get("must_advance_scene") is False or payload.get("transition", {}).get("transition_required") is True


def test_predicate_holds_plan_backed_auto_off_compact() -> None:
    common = dict(
        narration_obligations={"is_opening_scene": False, "must_advance_scene": False},
        resolution={},
        uncertainty_hint=None,
        follow_up_pressure=None,
        active_topic_anchor=None,
    )
    assert _should_use_manual_play_compact_prompt(prompt_profile="manual_play_auto", stamp_matched_narrative_plan=True, **common) is False
    advanced = dict(common)
    advanced["narration_obligations"] = {"is_opening_scene": False, "must_advance_scene": True}
    assert _should_use_manual_play_compact_prompt(prompt_profile="manual_play_auto", stamp_matched_narrative_plan=True, **advanced) is False
    assert _should_use_manual_play_compact_prompt(prompt_profile="manual_play_compact", stamp_matched_narrative_plan=True, **common) is True
    assert _should_use_manual_play_compact_prompt(prompt_profile="full", stamp_matched_narrative_plan=True, **common) is False
    assert _should_use_manual_play_compact_prompt(prompt_profile="manual_play_auto", stamp_matched_narrative_plan=False, **common) is True


def test_plan_backed_auto_keeps_full_instructions_when_transition_is_false() -> None:
    payload = _assemble("I examine the notice board.", "manual_play_auto")
    _assert_full_authority(payload)
    transition = payload.get("transition") if isinstance(payload.get("transition"), dict) else {}
    obligations = payload["narration_obligations"]
    assert transition.get("transition_required") is False
    assert transition.get("transition_type") == "none"
    assert obligations.get("must_advance_scene") is False
    assert len(payload["instructions"]) > 18


def test_plan_backed_auto_keeps_full_instructions_when_transition_is_true() -> None:
    payload = _assemble(
        "I walk through the gate into the district.",
        "manual_play_auto",
        resolution={"kind": "scene_transition", "resolved_transition": True, "target_scene_id": "old_milestone"},
        mutations={
            "scene": {"scene_id": "frontier_gate", "activate_scene_id": "old_milestone"},
            "session": {},
            "combat": {},
            "clues_leads": {},
        },
    )
    text = _joined(payload)
    transition = payload.get("transition") if isinstance(payload.get("transition"), dict) else {}
    assert _compact_enabled(payload) is False
    assert transition.get("transition_required") is True
    assert payload["narration_obligations"]["must_advance_scene"] is True
    assert _MUST_NOT in text
    assert _FIRST in text
    assert _SPEAKER in text
    assert _DRAFT in text
    assert isinstance(payload.get("first_mention_contract"), dict)


def test_explicit_compact_profile_still_compacts_a_plan_backed_request() -> None:
    full = _assemble("I examine the notice board.", "manual_play_auto")
    compact = _assemble("I examine the notice board.", "manual_play_compact")
    assert _compact_enabled(compact) is True
    assert _MUST_NOT not in _joined(compact)
    assert "first_mention_contract" not in compact
    assert len(compact["instructions"]) < len(full["instructions"])
    assert _MUST_NOT in _joined(full)


def test_detached_no_resolution_request_stays_compact() -> None:
    session, _body = _session("I wait and listen.")
    kwargs = _kwargs(session, "I wait and listen.", resolution={})
    ensure_narration_plan_bundle_for_manual_ctir_tests(session, kwargs)
    detach_ctir(session)
    payload = build_narration_context(**kwargs, prompt_profile="manual_play_auto", include_non_public_prompt_keys=True)
    assert payload.get("narrative_plan") is None
    assert payload.get("transition") is None
    assert _compact_enabled(payload) is True
    assert _MUST_NOT not in _joined(payload)
    assert session.get("active_scene_id") == "frontier_gate"


def test_same_text_without_a_plan_does_not_inherit_full_instructions() -> None:
    attached = _assemble("I wait and listen.", "manual_play_auto")
    session = {
        "active_scene_id": "frontier_gate",
        "turn_counter": 7,
        "visited_scene_ids": ["frontier_gate"],
        "interaction_context": {
            "active_interaction_target_id": None,
            "active_interaction_kind": None,
            "interaction_mode": "none",
        },
    }
    payload = build_narration_context(
        **_kwargs(session, "I wait and listen.", resolution={}),
        prompt_profile="manual_play_auto",
        include_non_public_prompt_keys=True,
    )
    assert _compact_enabled(attached) is False
    assert _MUST_NOT in _joined(attached)
    assert _compact_enabled(payload) is True
    assert _MUST_NOT not in _joined(payload)


def test_inspection_and_dialogue_keep_authority_without_a_location_change() -> None:
    inspection = _assemble("I look closely at the notice board.", "manual_play_auto")
    dialogue = _assemble("Hello, Gate Guard.", "manual_play_auto")
    ambiguous = _assemble("I try the thing by the board.", "manual_play_auto")
    for payload in (inspection, dialogue, ambiguous):
        _assert_full_authority(payload)
        transition = payload.get("transition") if isinstance(payload.get("transition"), dict) else {}
        assert transition.get("transition_required") is False
        assert transition.get("transition_type") == "none"
        assert payload["narration_obligations"]["must_advance_scene"] is False
    assert _SPEAKER in _joined(dialogue)


def test_assembled_instruction_list_is_stable() -> None:
    session, _body = _session("I examine the notice board.")
    kwargs = _kwargs(session, "I examine the notice board.")
    ensure_narration_plan_bundle_for_manual_ctir_tests(session, kwargs)
    first = build_narration_context(**copy.deepcopy(kwargs), prompt_profile="manual_play_auto")
    second = build_narration_context(**copy.deepcopy(kwargs), prompt_profile="manual_play_auto")
    assert first["instructions"] == second["instructions"]
    assert first["narration_obligations"]["must_advance_scene"] is False


def test_operational_refusal_is_not_completed_gameplay() -> None:
    classified = classify_operational_refusal("unresolved_retreat_without_adjudication")
    assert classified is not None
    assert classified["response_class"] == OPERATIONAL_REFUSAL
    assert classified["gameplay_executed"] is False
    assert classified["gameplay_publication_completed"] is False
    session = {
        "active_scene_id": "frontier_gate",
        "turn_counter": 16,
        "last_publication": {"visible": "The notice board is unchanged.", "final": True},
    }
    resolution = {"kind": "interpretation_rejected", "metadata": dict(classified)}
    assert note_completed_publication(session, text="You step back from the board.", resolution=resolution) is None
    assert session["last_publication"]["visible"] == "The notice board is unchanged."
    assert session["active_scene_id"] == "frontier_gate"
